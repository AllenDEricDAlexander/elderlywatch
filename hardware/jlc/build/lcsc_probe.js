const PARTS = __PARTS__;

const found = [];
const missing = [];

for (const part of PARTS) {
  const key = part.lcscId ? `C${part.lcscId.replace(/^C/i, "")}` : part.mpn;
  let items = [];
  try {
    items = await eda.lib_Device.search(key, undefined, undefined, undefined, 8, 1);
  } catch (err) {
    missing.push({ ref: part.ref, key, reason: String((err && err.message) || err) });
    continue;
  }
  if (!items || items.length === 0) {
    missing.push({ ref: part.ref, key, reason: "no hit" });
    continue;
  }
  found.push({
    ref: part.ref,
    key,
    hits: items.length,
    // Field names are not assumed from the docs: every own property is reported,
    // with nested objects/arrays flattened to a type tag so nothing is circular.
    candidates: items.map((i) => {
      const flat = {};
      for (const k of Object.keys(i)) {
        const v = i[k];
        flat[k] = v !== null && typeof v === "object"
          ? `[${Array.isArray(v) ? "array:" + v.length : typeof v}]`
          : v;
      }
      return flat;
    }),
  });
}

return { wanted: PARTS.length, found: found.length, missing, found };
