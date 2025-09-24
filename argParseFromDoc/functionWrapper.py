#!/usr/bin/env python3

import functools
import inspect
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, TypeVar, get_type_hints

F = TypeVar("F", bound=Callable[..., Any])

# --------------------------- Docstring helpers --------------------------------

def _detect_style(doc: str) -> str:
    if "@param" in doc:
        return "epydoc"
    if ":param" in doc:
        return "rest"
    if re.search(r"(?m)^\s*(Args|Arguments)\s*:", doc):
        return "google"
    if re.search(r"(?m)^\s*Parameters\s*\n\s*-{3,}\s*$", doc):
        return "numpy"
    return "epydoc"


def _extract_param_docs(doc: str, style: str) -> Dict[str, str]:
    """Extract {name: description} from the *parameter section* of the doc (best-effort)."""
    docs: Dict[str, str] = {}
    lines = doc.splitlines()

    if style == "epydoc":
        for line in lines:
            m = re.match(r"\s*@param\s+([A-Za-z_]\w*)\s*:\s*(.*)", line)
            if m:
                docs[m.group(1)] = m.group(2).strip()

    elif style == "rest":
        for line in lines:
            m = re.match(r"\s*:param\s+([A-Za-z_]\w*)\s*:\s*(.*)", line)
            if m:
                docs[m.group(1)] = m.group(2).strip()

    elif style == "google":
        # Only look inside the Args/Arguments block
        m = re.search(r"(?ms)^\s*(Args|Arguments)\s*:\s*(.+?)(?:\n\s*\n|$)", doc)
        if m:
            block = m.group(2)
            for line in block.splitlines():
                m2 = re.match(r"\s{2,}([A-Za-z_]\w*)\s*:\s*(.*)", line)
                if m2:
                    docs[m2.group(1)] = m2.group(2).strip()

    elif style == "numpy":
        # Only look inside the Parameters block
        m = re.search(r"(?ms)^\s*Parameters\s*\n\s*-{3,}\s*\n(.*?)(?=\n\S|\Z)", doc)
        if m:
            block = m.group(1)
            blines = block.splitlines()
            i = 0
            while i < len(blines):
                m2 = re.match(r"\s*([A-Za-z_]\w*)\s*:\s*(.*)", blines[i])
                if m2:
                    name = m2.group(1)
                    i += 1
                    desc_lines = []
                    while i < len(blines) and re.match(r"\s{2,}\S", blines[i]):
                        desc_lines.append(blines[i].strip())
                        i += 1
                    docs[name] = " ".join(desc_lines) if desc_lines else ""
                else:
                    i += 1

    return docs


def _split_doc_around_param_section(doc: str, style: str):
    """
    Return (pre, param_block, post), where param_block is the existing parameter section.
    If none is found, param_block is "", pre=doc, post="".
    """
    if not doc:
        return "", "", ""

    if style in ("epydoc", "rest"):
        marker = r"@param" if style == "epydoc" else r":param"
        lines = doc.splitlines()
        idxs = [i for i, ln in enumerate(lines) if re.match(rf"\s*{marker}\b", ln)]
        if not idxs:
            return doc, "", ""
        first_i, last_i = idxs[0], idxs[-1]
        pre = "\n".join(lines[:first_i]).rstrip()
        param_block = "\n".join(lines[first_i:last_i + 1]).strip("\n")
        post = "\n".join(lines[last_i + 1:]).lstrip("\n")
        return pre, param_block, post

    if style == "google":
        m = re.search(r"(?ms)^\s*(Args|Arguments)\s*:\s*.+?(?:\n\s*\n|$)", doc)
        if not m:
            return doc, "", ""
        pre = doc[:m.start()].rstrip()
        param_block = doc[m.start():m.end()].strip("\n")
        post = doc[m.end():].lstrip("\n")
        return pre, param_block, post

    if style == "numpy":
        m = re.search(r"(?ms)^\s*Parameters\s*\n\s*-{3,}\s*\n.*?(?=\n\S|\Z)", doc)
        if not m:
            return doc, "", ""
        pre = doc[:m.start()].rstrip()
        param_block = doc[m.start():m.end()].strip("\n")
        post = doc[m.end():].lstrip("\n")
        return pre, param_block, post

    return doc, "", ""


def _ann_to_str(ann: Any) -> str:
    if ann is inspect._empty:
        return "Any"
    if hasattr(ann, "__name__"):
        return ann.__name__
    return str(ann)


def _render_params(style: str, ordered_names, name_to_desc: Dict[str, str], annotations: Dict[str, Any]) -> str:
    if style == "google":
        out = ["Args:"]
        for name in ordered_names:
            out.append(f"    {name}: {name_to_desc.get(name, '')}")
        return "\n".join(out)

    if style == "numpy":
        out = ["Parameters", "----------"]
        for name in ordered_names:
            out.append(f"{name} : {_ann_to_str(annotations.get(name, Any))}")
            desc = name_to_desc.get(name, "")
            if desc:
                out.append(f"    {desc}")
        return "\n".join(out)

    if style == "rest":
        return "\n".join([f":param {name}: {name_to_desc.get(name, '')}" for name in ordered_names])

    # epydoc
    return "\n".join([f"@param {name}: {name_to_desc.get(name, '')}" for name in ordered_names])


def _compose_doc_in_signature_order(
    original_doc: str | None,
    ordered_param_names: list[str],
    annotations: Dict[str, Any],
    extra_param_docs: Dict[str, str],
    prefix: str = "",
    suffix: str = "",
    replace_prefix: bool = False,
    replace_suffix: bool = False,
) -> str:
    """
    Rebuild docstring param block to match the signature order exactly.
    Keep original style and other content. Optionally replace or keep the
    original prefix/suffix content. Append provided prefix/suffix accordingly.
    """
    original_doc = original_doc or ""
    style = _detect_style(original_doc)

    pre, param_block, post = _split_doc_around_param_section(original_doc, style)
    existing_docs = _extract_param_docs(param_block or original_doc, style)

    # Merge descriptions: prefer existing, then supplied extra docs
    merged_descs = {}
    merged_descs.update({k: v for k, v in existing_docs.items() if v})
    merged_descs.update({k: v for k, v in extra_param_docs.items() if v})

    new_param_block = _render_params(style, ordered_param_names, merged_descs, annotations)

    # Build final prefix and suffix regions
    pre_final = ""
    if replace_prefix:
        pre_final = prefix.strip() if prefix else ""
    else:
        pre_final = pre.strip()
        if prefix:
            pre_final = (prefix.strip() if not pre_final else f"{pre_final}\n\n{prefix.strip()}")

    post_final = ""
    if replace_suffix:
        post_final = suffix.strip() if suffix else ""
    else:
        post_final = post.strip()
        if suffix:
            post_final = (suffix.strip() if not post_final else f"{post_final}\n\n{suffix.strip()}")

    # Stitch together: [pre_final] + blank + [new_param_block] + blank + [post_final]
    parts = []
    if pre_final:
        parts.append(pre_final)
    parts.append(new_param_block)  # params should be present even if prefix/suffix empty
    if post_final:
        parts.append(post_final)
    return "\n\n".join(parts)


# --------------------------- Wrapper builder ----------------------------------

@dataclass
class _DocParam:
    name: str
    annotation: Any
    description: str


def create_wrapper_with_extra_args(
    original_func: F,
    *,
    extra_args: Dict[str, Any] | None = None,               # new POSITIONAL_OR_KEYWORD (with defaults)
    extra_kwargs: Dict[str, Any] | None = None,             # new KEYWORD_ONLY
    extra_args_types: Dict[str, Any] | None = None,         # types for extra_args
    extra_kwargs_types: Dict[str, Any] | None = None,       # types for extra_kwargs
    extra_param_docs: Dict[str, str] | None = None,         # docs for new params
    docstring_prefix: str = "",
    docstring_suffix: str = "",
    replace_prefix: bool = False,
    replace_suffix: bool = False,
) -> F:
    """
    Create a wrapper that adds new parameters without changing original logic,
    preserving signature, type hints, and docstring style. The parameter
    documentation is rebuilt to exactly follow the wrapper signature order.

    Args:
        original_func: function to wrap
        extra_args: dict of new POSITIONAL_OR_KEYWORD params (with defaults)
        extra_kwargs: dict of new KEYWORD_ONLY params (with defaults)
        extra_args_types: explicit types for extra_args (name->type)
        extra_kwargs_types: explicit types for extra_kwargs (name->type)
        extra_param_docs: descriptions for new params (name->str)
        docstring_prefix: text to place before the main content
        docstring_suffix: text to place after the main content
        replace_prefix: if True, replace any existing prefix text with docstring_prefix
        replace_suffix: if True, replace any existing suffix text with docstring_suffix
    """
    extra_args = extra_args or {}
    extra_kwargs = extra_kwargs or {}
    extra_args_types = extra_args_types or {}
    extra_kwargs_types = extra_kwargs_types or {}
    extra_param_docs = extra_param_docs or {}

    orig_sig = inspect.signature(original_func)
    orig_params = list(orig_sig.parameters.values())

    # Partition original to keep legal ordering
    posonly_no = [p for p in orig_params if p.kind == inspect.Parameter.POSITIONAL_ONLY and p.default is inspect._empty]
    posonly_def = [p for p in orig_params if p.kind == inspect.Parameter.POSITIONAL_ONLY and p.default is not inspect._empty]
    posorkw_no = [p for p in orig_params if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and p.default is inspect._empty]
    posorkw_def = [p for p in orig_params if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and p.default is not inspect._empty]
    kwonly     = [p for p in orig_params if p.kind == inspect.Parameter.KEYWORD_ONLY]
    varpos     = next((p for p in orig_params if p.kind == inspect.Parameter.VAR_POSITIONAL), None)
    varkw      = next((p for p in orig_params if p.kind == inspect.Parameter.VAR_KEYWORD), None)

    # Build new params
    extra_posorkw = [
        inspect.Parameter(
            name,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=default,
            annotation=extra_args_types.get(name, Any if default is None else type(default)),
        )
        for name, default in extra_args.items()
    ]
    extra_kwonly_params = [
        inspect.Parameter(
            name,
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=default,
            annotation=extra_kwargs_types.get(name, Any if default is None else type(default)),
        )
        for name, default in extra_kwargs.items()
    ]

    # Compose new signature
    new_params: list[inspect.Parameter] = []
    new_params += posonly_no
    new_params += posorkw_no
    new_params += extra_posorkw               # new optional POK after requireds
    new_params += posonly_def
    new_params += posorkw_def
    if varpos:
        new_params.append(varpos)
    new_params += kwonly
    new_params += extra_kwonly_params
    if varkw:
        new_params.append(varkw)

    new_sig = orig_sig.replace(parameters=new_params)

    # Merge type hints
    try:
        new_annotations = dict(get_type_hints(original_func))
    except Exception:
        new_annotations = dict(getattr(original_func, "__annotations__", {}))
    for p in extra_posorkw:
        new_annotations[p.name] = p.annotation
    for p in extra_kwonly_params:
        new_annotations[p.name] = p.annotation

    ordered_param_names = [
        p.name for p in new_sig.parameters.values()
        if p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]

    @functools.wraps(original_func)
    def wrapper(*args, **kwargs):
        bound = new_sig.bind(*args, **kwargs)
        bound.apply_defaults()

        call_pos = []
        call_kw = {}
        # Forward only original function's parameters
        for p in orig_params:
            if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                call_pos.append(bound.arguments[p.name])
            elif p.kind == inspect.Parameter.VAR_POSITIONAL:
                call_pos.extend(bound.arguments.get(p.name, ()))
            elif p.kind == inspect.Parameter.KEYWORD_ONLY:
                call_kw[p.name] = bound.arguments[p.name]
            elif p.kind == inspect.Parameter.VAR_KEYWORD:
                call_kw.update(bound.arguments.get(p.name, {}))
        return original_func(*call_pos, **call_kw)

    wrapper.__signature__ = new_sig
    wrapper.__annotations__ = new_annotations
    wrapper.__doc__ = _compose_doc_in_signature_order(
        original_func.__doc__ or "",
        ordered_param_names,
        new_annotations,
        extra_param_docs,
        prefix=docstring_prefix,
        suffix=docstring_suffix,
        replace_prefix=replace_prefix,
        replace_suffix=replace_suffix,
    )
    return wrapper

# ----------------------------- Demo & tests -----------------------------------




if __name__ == "__main__":
    def calculate_area(length: float, width: float, height: float = 1.0) -> float:
        """
        Calculate the area or volume of a rectangle.

        @param length: Length of the rectangle
        @param width: Width of the rectangle
        @param height: Height for volume calculation (default: 1.0 for area)
        """
        return length * width * height


    def _demo_build_wrapper() -> Callable[..., Any]:
        enhanced = create_wrapper_with_extra_args(
            calculate_area,
            extra_args={"scale_factor": 1.0},
            extra_kwargs={"unit": "m2", "precision": 2},
            extra_args_types={"scale_factor": float},
            extra_kwargs_types={"unit": str, "precision": int},
            extra_param_docs={
                "scale_factor": "Scaling factor (for docs/CLI; logic unchanged).",
                "unit": "Display units (for docs/CLI).",
                "precision": "Number of decimals (for docs/CLI).",
            },
            docstring_prefix="Enhanced wrapper: adds formatting parameters but keeps original behavior.",
            docstring_suffix="Notes:\n    Extra parameters are for documentation/CLI only; computation is unchanged.",
            replace_prefix=False,  # keep original intro text, then add prefix after it
            replace_suffix=False,  # keep any trailing sections, then append suffix
        )
        return enhanced


    def _sanity(enhanced):
        print("Original signature:", inspect.signature(calculate_area))
        print("Wrapper signature:", inspect.signature(enhanced))
        print("\nOriginal annotations:", calculate_area.__annotations__)
        print("Wrapper annotations:", enhanced.__annotations__)
        print("\nWrapper docstring:\n", enhanced.__doc__)
        res = enhanced(5.0, 3.0, scale_factor=2.0, unit="cm2", precision=1)
        print(f"\nFunction call result (logic unchanged): {res}")

    enhanced_calculate = _demo_build_wrapper()
    _sanity(enhanced_calculate)

    # CLI test with argParseFromDoc:
    #   pip install argParseFromDoc
    # Example:
    #   python this_script.py --length 5 --width 3 --height 1 --scale-factor 2 --unit cm2 --precision 1
    from argParseFromDoc import parse_function_and_call
    parse_function_and_call(enhanced_calculate)
