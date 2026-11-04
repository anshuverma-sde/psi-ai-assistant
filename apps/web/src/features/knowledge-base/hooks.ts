"use client";

import { useApiMutation, useApiQuery } from "@/shared/api/hooks";
import type { DocumentListOut } from "@/shared/api/types";
import { documentsApi, documentsKey } from "./api";

const isBusy = (data?: DocumentListOut) =>
  !!data?.documents.some((d) => d.status === "PENDING" || d.status === "PROCESSING");

/** Polls while any document is still being processed. */
export function useDocuments() {
  return useApiQuery(documentsKey, documentsApi.list, {
    refetchInterval: (query) => (isBusy(query.state.data) ? 1500 : false),
  });
}

export const useUploadDocument = () =>
  useApiMutation(documentsApi.upload, {
    invalidate: [documentsKey],
    toastErrors: false, // UploadPanel lists per-file errors inline
    successMessage: (doc) => `Uploaded ${doc.original_name} — processing…`,
  });

export const useReplaceDocument = () =>
  useApiMutation(documentsApi.replace, {
    invalidate: [documentsKey],
    successMessage: (doc) => `Replaced with ${doc.original_name} — processing…`,
  });

export const useDeleteDocument = () =>
  useApiMutation(documentsApi.remove, { invalidate: [documentsKey], successMessage: "Document deleted" });
