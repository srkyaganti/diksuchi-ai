/**
 * Serializes a file record by converting BigInt fields to strings
 */
export function serializeFile(file: any) {
  return {
    ...file,
    fileSize: file.fileSize.toString(),
  };
}

/**
 * Serializes an array of file records
 */
export function serializeFiles(files: any[]) {
  return files.map(serializeFile);
}
