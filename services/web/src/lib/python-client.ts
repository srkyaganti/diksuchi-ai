/**
 * RAG Service Client
 *
 * Typed interfaces for communicating with the Python RAG service
 * (document processing, job management, and hybrid retrieval).
 */

const PYTHON_WORKER_URL = process.env.PYTHON_WORKER_URL || "http://localhost:5001";

export interface ProcessJobRequest {
  fileId: string;
  collectionId: string;
  fileName: string;
  filePath: string;
  mimeType: string;
  uuid: string;
}

export interface ProcessJobResponse {
  jobId: string;
  status: string;
  message: string;
}

export interface JobStatusResponse {
  jobId: string;
  status: string;
  progress?: number;
  error?: string;
}

export interface RetrieveRequest {
  query: string;
  collectionId: string;
  topK?: number;
}

export interface SectionResult {
  content: string;
  sectionPath: string;
  sectionId: string;
  documentUuid: string;
  score: number;
}

export interface RetrieveResponse {
  sections: SectionResult[];
  timingMs: number;
}

export class RAGServiceClient {
  private workerUrl: string;
  private timeout: number;

  constructor(
    workerUrl: string = PYTHON_WORKER_URL,
    timeout: number = 120000,
  ) {
    this.workerUrl = workerUrl;
    this.timeout = timeout;
  }

  async submitProcessingJob(job: ProcessJobRequest): Promise<ProcessJobResponse> {
    const url = `${this.workerUrl}/api/process`;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(job),
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(
          `Document processing error (${response.status}): ${error.detail || error.message || "Unknown error"}`
        );
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === "AbortError") {
        throw new Error("Document processing request timed out");
      }
      if (error.code === "ECONNREFUSED") {
        throw new Error("Document processing service is not reachable. Is the service running?");
      }
      throw error;
    }
  }

  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const url = `${this.workerUrl}/api/jobs/${jobId}`;

    try {
      const response = await fetch(url, {
        method: "GET",
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(
          `Failed to get job status (${response.status}): ${error.detail || error.message}`
        );
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === "AbortError") {
        throw new Error("Job status request timed out");
      }
      throw error;
    }
  }

  async retrieveDocuments(req: RetrieveRequest): Promise<RetrieveResponse> {
    const url = `${this.workerUrl}/api/retrieve`;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
        signal: AbortSignal.timeout(30000),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(
          `Retrieval error (${response.status}): ${error.detail || error.message || "Unknown error"}`
        );
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === "AbortError") {
        throw new Error("Retrieval request timed out");
      }
      if (error.code === "ECONNREFUSED") {
        throw new Error("RAG service is not reachable. Is the service running?");
      }
      throw error;
    }
  }

  async healthCheck(): Promise<boolean> {
    const url = `${this.workerUrl}/health`;

    try {
      const response = await fetch(url, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });

      return response.ok;
    } catch {
      return false;
    }
  }
}

export const ragClient = new RAGServiceClient();

export async function submitDocumentProcessing(job: ProcessJobRequest): Promise<ProcessJobResponse> {
  return ragClient.submitProcessingJob(job);
}

export async function retrieveDocuments(req: RetrieveRequest): Promise<RetrieveResponse> {
  return ragClient.retrieveDocuments(req);
}

export async function checkProcessingServiceHealth(): Promise<boolean> {
  return ragClient.healthCheck();
}
