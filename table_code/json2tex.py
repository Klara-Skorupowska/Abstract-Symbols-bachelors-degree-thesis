import json
from pathlib import Path


def escape_tex(text):
  """Escapes special LaTeX characters in strings."""
  if text is None:
    return ""
  replacements = {
      "\\": r"\textbackslash{}",
      "&": r"\&",
      "%": r"\%",
      "$": r"\$",
      "#": r"\#",
      "_": r"\_",
      "{": r"\{",
      "}": r"\}",
      "~": r"\textasciitilde{}",
      "^": r"\textasciicircum{}",
  }
  return "".join(replacements.get(c, c) for c in str(text))


def to_comparable_number(val):
  """Converts ints, floats (including negatives), and HH:MM:SS strings to float for comparison.

  Returns None if the value is not numeric/time.
  """
  if val is None or isinstance(val, bool):
    return None
  if isinstance(val, (int, float)):
    return float(val)

  s = str(val).strip()
  # Handle HH:MM:SS or MM:SS duration strings
  if ":" in s and not any(c.isalpha() for c in s):
    parts = s.split(":")
    try:
      nums = [float(p) for p in parts]
      if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
      elif len(nums) == 2:
        return nums[0] * 60 + nums[1]
    except ValueError:
      return None

  try:
    return float(s)
  except ValueError:
    return None


def format_cell(key, value, highlight=None):
  """Formats cell values, stacking comma-separated parameters and applying bold/asterisks."""
  text = str(value) if value is not None else ""

  if key.lower() == "parameter" and "," in text:
    parts = [escape_tex(part.strip()) for part in text.split(",")]
    return r" \newline ".join(parts)

  escaped = escape_tex(text)
  if highlight == "max":
    return f"\\textbf{{{escaped}**}}"
  elif highlight == "min":
    return f"\\textbf{{{escaped}*}}"
  return escaped


def convert_json_to_tex(json_filepath):
  json_path = Path(json_filepath)
  tex_path = json_path.with_suffix(".tex")

  with open(json_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

  if isinstance(raw_data, dict):
    rows = list(raw_data.values())
  elif isinstance(raw_data, list):
    rows = raw_data
  else:
    raise ValueError("JSON root must be a list or an object.")

  if not rows:
    raise ValueError("JSON data is empty.")

  # Keys excluding the first column (ID)
  keys = list(rows[0].keys())[1:]

  # Pre-compute min and max per column
  col_extrema = {}
  for k in keys:
    if k.lower() == "parameter":
      continue
    nums = [
        to_comparable_number(row.get(k))
        for row in rows
        if to_comparable_number(row.get(k)) is not None
    ]
    # Only highlight if there are numbers and they are NOT all identical
    if len(nums) > 1 and min(nums) != max(nums):
      col_extrema[k] = (min(nums), max(nums))

  with open(tex_path, "w", encoding="utf-8") as out:
    for row in rows:
      cells = []
      for k in keys:
        val = row.get(k)
        highlight = None
        if k in col_extrema:
          num = to_comparable_number(val)
          if num is not None:
            col_min, col_max = col_extrema[k]
            if num == col_max:
              highlight = "max"
            elif num == col_min:
              highlight = "min"
        cells.append(format_cell(k, val, highlight))

      out.write(" & ".join(cells) + " \\\\\n\\addlinespace\n")


convert_json_to_tex("table_code/experiments_summary.json")