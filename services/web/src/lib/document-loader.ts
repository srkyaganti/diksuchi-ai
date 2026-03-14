/**
 * Document Loader
 *
 * Reads processed document files from the storage directory.
 * Used for document viewing / preview in the UI. Chat retrieval
 * is now handled by the RAG service's /api/retrieve endpoint.
 */

import { readFile } from "fs/promises";
import { existsSync } from "fs";
import { join } from "path";
import prisma from "@/lib/prisma";

const STORAGE_PATH =
  process.env.DOCLING_STORAGE_PATH || join(process.cwd(), "storage");

export interface DocumentContent {
  fileId: string;
  fileName: string;
  uuid: string;
  textContent: string;
  imageRefs: ImageRef[];
}

export interface ImageRef {
  filename: string;
  caption?: string;
  page?: number;
}

/**
 * Load all processed documents for a collection.
 * Reads document.md (or legacy document.json) from storage/{uuid}/.
 */
export async function loadCollectionDocuments(
  collectionId: string,
): Promise<DocumentContent[]> {
  const files = await prisma.file.findMany({
    where: {
      collectionId,
      ragStatus: "completed",
    },
    select: {
      id: true,
      name: true,
      uuid: true,
    },
  });

  const documents: DocumentContent[] = [];

  for (const file of files) {
    const mdPath = join(STORAGE_PATH, file.uuid, "document.md");
    const jsonPath = join(STORAGE_PATH, file.uuid, "document.json");

    try {
      let textContent: string;
      let imageRefs: ImageRef[] = [];

      if (existsSync(mdPath)) {
        textContent = await readFile(mdPath, "utf-8");
        imageRefs = extractImageRefsFromMarkdown(textContent);
      } else if (existsSync(jsonPath)) {
        const raw = await readFile(jsonPath, "utf-8");
        const doclingJson = JSON.parse(raw);
        textContent = extractTextContent(doclingJson);
        imageRefs = extractImageReferences(doclingJson);
      } else {
        console.warn(
          `No document.md or document.json for file ${file.name} (${file.uuid})`,
        );
        continue;
      }

      documents.push({
        fileId: file.id,
        fileName: file.name,
        uuid: file.uuid,
        textContent,
        imageRefs,
      });
    } catch (err) {
      console.error(
        `Failed to load document for ${file.name} (${file.uuid}):`,
        err,
      );
    }
  }

  return documents;
}

/**
 * Extract image references from markdown content (![alt](path) patterns).
 */
function extractImageRefsFromMarkdown(markdown: string): ImageRef[] {
  const refs: ImageRef[] = [];
  const imgRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  let match;
  let counter = 0;
  while ((match = imgRegex.exec(markdown)) !== null) {
    counter++;
    refs.push({
      filename: match[2].split("/").pop() || `image_${counter}.png`,
      caption: match[1] || undefined,
    });
  }
  return refs;
}

// --- Legacy JSON support below ---

function extractTextContent(doc: any): string {
  const parts: string[] = [];

  if (doc.texts) {
    for (const item of doc.texts) {
      const label = item.label || "";
      const text = item.text || "";
      if (!text.trim()) continue;

      if (label === "section_header" || label === "title") {
        parts.push(`\n## ${text}\n`);
      } else if (label === "page_header" || label === "page_footer") {
        continue;
      } else {
        parts.push(text);
      }
    }
  }

  if (doc.tables) {
    for (const table of doc.tables) {
      if (table.data && table.data.table_cells) {
        const rendered = renderTable(table.data);
        if (rendered) parts.push(rendered);
      }
    }
  }

  if (doc.pictures) {
    for (const pic of doc.pictures) {
      const caption = pic.caption_text || pic.caption || "";
      if (caption) {
        parts.push(`[Image: ${caption}]`);
      }
    }
  }

  return parts.join("\n\n");
}

function renderTable(tableData: any): string {
  if (!tableData.table_cells || tableData.table_cells.length === 0) return "";

  const maxRow = Math.max(
    ...tableData.table_cells.map(
      (c: any) => c.end_row_offset_idx ?? c.row ?? 0,
    ),
  );
  const maxCol = Math.max(
    ...tableData.table_cells.map(
      (c: any) => c.end_col_offset_idx ?? c.col ?? 0,
    ),
  );

  if (maxRow === 0 || maxCol === 0) return "";

  const grid: string[][] = Array.from({ length: maxRow }, () =>
    Array.from({ length: maxCol }, () => ""),
  );

  for (const cell of tableData.table_cells) {
    const r = cell.start_row_offset_idx ?? cell.row ?? 0;
    const c = cell.start_col_offset_idx ?? cell.col ?? 0;
    if (r < maxRow && c < maxCol) {
      grid[r][c] = (cell.text || "").replace(/\n/g, " ");
    }
  }

  const lines: string[] = [];
  lines.push("| " + grid[0].join(" | ") + " |");
  lines.push("|" + grid[0].map(() => "---").join("|") + "|");
  for (let r = 1; r < grid.length; r++) {
    lines.push("| " + grid[r].join(" | ") + " |");
  }
  return lines.join("\n");
}

function extractImageReferences(doc: any): ImageRef[] {
  const refs: ImageRef[] = [];

  if (doc.pictures) {
    for (let i = 0; i < doc.pictures.length; i++) {
      const pic = doc.pictures[i];
      refs.push({
        filename: `picture_${i + 1}.png`,
        caption: pic.caption_text || pic.caption || undefined,
        page: pic.prov?.[0]?.page_no || undefined,
      });
    }
  }

  return refs;
}
