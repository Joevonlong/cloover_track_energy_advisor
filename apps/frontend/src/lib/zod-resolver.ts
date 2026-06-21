// Minimal RHF resolver for Zod — avoids pulling in @hookform/resolvers (not
// installed, and the pnpm/npm split in this repo makes adding deps risky).
//
// On success it returns the parsed/coerced OUTPUT (numbers, not the raw input
// strings), so handleSubmit receives a clean object. On failure it maps Zod
// issues onto RHF's nested error tree (e.g. ["heating","eur_month"]).
import type { FieldErrors, FieldValues, Resolver } from "react-hook-form";
import type { ZodType, ZodTypeDef } from "zod";

type ErrorTree = Record<string, unknown>;

function placeIssue(tree: ErrorTree, path: string[], node: { type: string; message: string }) {
  let cursor = tree;
  for (let i = 0; i < path.length - 1; i += 1) {
    const key = path[i];
    const existing = cursor[key];
    // Replace a leaf error node with a branch if a deeper path needs it.
    if (typeof existing !== "object" || existing === null || "message" in (existing as object)) {
      cursor[key] = {};
    }
    cursor = cursor[key] as ErrorTree;
  }
  const leaf = path[path.length - 1];
  if (cursor[leaf] === undefined) {
    cursor[leaf] = node; // first issue per field wins
  }
}

export function zodResolver<TInput extends FieldValues, TOutput>(
  schema: ZodType<TOutput, ZodTypeDef, unknown>,
): Resolver<TInput, unknown, TOutput> {
  return async (values) => {
    const result = schema.safeParse(values);
    if (result.success) {
      return { values: result.data, errors: {} };
    }

    const errors: ErrorTree = {};
    for (const issue of result.error.issues) {
      const path = issue.path.map((segment) => String(segment));
      if (path.length > 0) {
        placeIssue(errors, path, { type: issue.code, message: issue.message });
      }
    }

    return { values: {}, errors: errors as FieldErrors<TInput> };
  };
}
