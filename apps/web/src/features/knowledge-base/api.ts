import { api } from "@/shared/api/client";
import type { Deleted, DocumentListOut, DocumentOut } from "@/shared/api/types";

export const documentsKey = ["documents"] as const;

export const documentsApi = {
  list: (signal?: AbortSignal) => api.get<DocumentListOut>("/api/admin/documents", signal),
  upload: (file: File) => api.upload<DocumentOut>("/api/admin/documents", file),
  replace: ({ id, file }: { id: string; file: File }) => api.upload<DocumentOut>(`/api/admin/documents/${id}`, file, "PUT"),
  remove: (id: string) => api.delete<Deleted>(`/api/admin/documents/${id}`),
};
