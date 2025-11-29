/**
 * Python RAG Service Client
 *
 * Provides typed interfaces for communicating with the Python RAG service.
 */

const PYTHON_WORKER_URL = process.env.PYTHON_WORKER_URL || "http://localhost:5000";
const PYTHON_RETRIEVAL_URL = process.env.PYTHON_RETRIEVAL_URL || "http://localhost:5000";

// Request/Response Types
export interface ProcessJobRequest {
  fileId: string;
  collectionId: string;
  fileName: string;
  filePath: string;
  mimeType: string;
}

export interface ProcessJobResponse {
  jobId: string;
  status: string;
  message: string;
}

export interface ChatMessage {
  role: string;  // "user" or "assistant"
  content: string;
}

export interface RetrieveRequest {
  query: string;
  collectionId: string;
  limit?: number;
  rerank?: boolean;
  chatHistory?: ChatMessage[];  // For conversational retrieval
  useConversationalRetrieval?: boolean;  // Enable conversation-aware retrieval
  conversationDepth?: number;  // How many turns to consider (default 3)
}

export interface RetrieveResult {
  content: string;
  fileId?: string;
  fileName?: string;
  similarity: number;
  metadata: Record<string, any>;
}

export interface RetrieveResponse {
  results: RetrieveResult[];
  total: number;
}

export interface JobStatusResponse {
  jobId: string;
  status: string;
  progress?: number;
  error?: string;
}

/**
 * Python RAG Service Client Class
 */
export class PythonRAGClient {
  private workerUrl: string;
  private retrievalUrl: string;
  private timeout: number;

  constructor(
    workerUrl: string = PYTHON_WORKER_URL,
    retrievalUrl: string = PYTHON_RETRIEVAL_URL,
    timeout: number = 30000
  ) {
    this.workerUrl = workerUrl;
    this.retrievalUrl = retrievalUrl;
    this.timeout = timeout;
  }

  /**
   * Submit a document processing job to the Python worker.
   */
  async submitProcessingJob(job: ProcessJobRequest): Promise<ProcessJobResponse> {
    const url = `${this.workerUrl}/api/process`;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(job),
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(
          `Python worker error (${response.status}): ${error.detail || error.message || "Unknown error"}`
        );
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === "AbortError") {
        throw new Error("Python worker request timed out");
      }
      if (error.code === "ECONNREFUSED") {
        throw new Error("Python worker is not reachable. Is the service running?");
      }
      throw error;
    }
  }

  /**
   * Get the status of a processing job.
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const url = `${this.workerUrl}/api/jobs/${jobId}`;

    try {
      const response = await fetch(url, {
        method: "GET",
        signal: AbortSignal.timeout(10000), // Shorter timeout for status checks
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

  /**
   * Perform hybrid retrieval with optional reranking.
   * Supports conversational retrieval when chatHistory is provided.
   */
  async retrieve(request: RetrieveRequest): Promise<RetrieveResponse> {
    const url = `${this.retrievalUrl}/api/retrieve`;

    const body: any = {
      query: request.query,
      collectionId: request.collectionId,
      limit: request.limit || 5,
      rerank: request.rerank !== false, // Default to true
    };

    // Add conversational retrieval parameters if provided
    if (request.chatHistory && request.chatHistory.length > 0) {
      body.chatHistory = request.chatHistory;
      body.useConversationalRetrieval = request.useConversationalRetrieval !== false; // Default to true if history provided
      body.conversationDepth = request.conversationDepth || 3;
    }

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(this.timeout),
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
        throw new Error("Python retrieval service is not reachable. Is the service running?");
      }
      throw error;
    }
  }

  /**
   * Check if the Python service is healthy.
   */
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

// Default client instance
export const pythonClient = new PythonRAGClient();

// Convenience functions
export async function submitDocumentProcessing(job: ProcessJobRequest): Promise<ProcessJobResponse> {
  return pythonClient.submitProcessingJob(job);
}

export async function retrieveContext(
  query: string,
  collectionId: string,
  limit: number = 5,
  rerank: boolean = true
): Promise<RetrieveResponse> {
  return pythonClient.retrieve({ query, collectionId, limit, rerank });
}

export async function checkPythonServiceHealth(): Promise<boolean> {
  return pythonClient.healthCheck();
}
