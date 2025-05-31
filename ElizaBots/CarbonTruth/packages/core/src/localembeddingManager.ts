import path from "node:path";
import { fileURLToPath } from "url";
import { FlagEmbedding, EmbeddingModel } from "fastembed";
import elizaLogger from "./logger";

class LocalEmbeddingModelManager {
    private static instance: LocalEmbeddingModelManager | null;
    private model: FlagEmbedding | null = null;
    private initPromise: Promise<void> | null = null;
    private initializationLock = false;

    private constructor() {}

    public static getInstance(): LocalEmbeddingModelManager {
        if (!LocalEmbeddingModelManager.instance) {
            LocalEmbeddingModelManager.instance =
                new LocalEmbeddingModelManager();
        }
        return LocalEmbeddingModelManager.instance;
    }

    private async getRootPath(): Promise<string> {
        const __filename = fileURLToPath(import.meta.url);
        const __dirname = path.dirname(__filename);
        const rootPath = path.resolve(__dirname, "..");
        return rootPath.includes("/eliza/")
            ? rootPath.split("/eliza/")[0] + "/eliza/"
            : path.resolve(__dirname, "..");
    }

    public async initialize(): Promise<void> {
        // If already initialized, return immediately
        if (this.model) {
            return;
        }

        // If initialization is in progress, wait for it
        if (this.initPromise) {
            return this.initPromise;
        }

        // Use a lock to prevent multiple simultaneous initializations
        if (this.initializationLock) {
            // Wait for current initialization to complete
            while (this.initializationLock) {
                await new Promise((resolve) => setTimeout(resolve, 100));
            }
            return;
        }

        this.initializationLock = true;

        try {
            this.initPromise = this.initializeModel();
            await this.initPromise;
        } finally {
            this.initializationLock = false;
            this.initPromise = null;
        }
    }

    private async initializeModel(): Promise<void> {
        const isNode =
            typeof process !== "undefined" &&
            process.versions != null &&
            process.versions.node != null;

        if (!isNode) {
            throw new Error("Local embedding not supported in browser");
        }

        const fs = await import("fs");
        const cacheDir = (await this.getRootPath()) + "/cache/";

        try {
            if (!fs.existsSync(cacheDir)) {
                fs.mkdirSync(cacheDir, { recursive: true });
            }

            elizaLogger.debug("Initializing BGE embedding model...");
            elizaLogger.debug("Cache directory:", cacheDir);

            this.model = await FlagEmbedding.init({
                cacheDir: cacheDir,
                model: EmbeddingModel.BGESmallENV15,
                maxLength: 512,
            });

            elizaLogger.debug("BGE model initialized successfully");
        } catch (error) {
            elizaLogger.error("Failed to initialize BGE model:", error);
            elizaLogger.info("Attempting to reinstall BGE model...");
            
            try {
                // Clear cache and reinstall
                await this.clearCacheAndReinstall(fs, cacheDir);
            } catch (reinstallError) {
                elizaLogger.error("Failed to reinstall BGE model:", reinstallError);
                // Reset state on failure
                this.model = null;
                this.initPromise = null;
                this.initializationLock = false;
                throw reinstallError;
            }
        }
    }

    private async clearCacheAndReinstall(fs: any, cacheDir: string): Promise<void> {
        elizaLogger.debug("Clearing cache directory for reinstallation...");
        
        // Remove existing cache directory
        if (fs.existsSync(cacheDir)) {
            fs.rmSync(cacheDir, { recursive: true, force: true });
            elizaLogger.debug("Cache directory removed");
        }
        
        // Recreate cache directory
        fs.mkdirSync(cacheDir, { recursive: true });
        elizaLogger.debug("Cache directory recreated");
        
        // Attempt to initialize again
        elizaLogger.debug("Reinstalling BGE embedding model...");
        
        this.model = await FlagEmbedding.init({
            cacheDir: cacheDir,
            model: EmbeddingModel.BGESmallENV15,
            maxLength: 512,
        });
        
        elizaLogger.info("BGE model reinstalled successfully");
    }

    public async generateEmbedding(input: string): Promise<number[]> {
        if (!this.model) {
            await this.initialize();
        }

        if (!this.model) {
            throw new Error("Failed to initialize model");
        }

        try {
            // Let fastembed handle tokenization internally
            const embedding = await this.model.queryEmbed(input);
            // Debug the raw embedding - uncomment if debugging embeddings
            // elizaLogger.debug("Raw embedding from BGE:", {
            //     type: typeof embedding,
            //     isArray: Array.isArray(embedding),
            //     dimensions: Array.isArray(embedding)
            //         ? embedding.length
            //         : "not an array",
            //     sample: Array.isArray(embedding)
            //         ? embedding.slice(0, 5)
            //         : embedding,
            // });
            return this.processEmbedding(embedding);
        } catch (error) {
            elizaLogger.error("Embedding generation failed:", error);
            throw error;
        }
    }

    private processEmbedding(embedding: number[]): number[] {
        let finalEmbedding: number[];

        if (
            ArrayBuffer.isView(embedding) &&
            embedding.constructor === Float32Array
        ) {
            finalEmbedding = Array.from(embedding);
        } else if (
            Array.isArray(embedding) &&
            ArrayBuffer.isView(embedding[0]) &&
            embedding[0].constructor === Float32Array
        ) {
            finalEmbedding = Array.from(embedding[0]);
        } else if (Array.isArray(embedding)) {
            finalEmbedding = embedding;
        } else {
            throw new Error(`Unexpected embedding format: ${typeof embedding}`);
        }

        finalEmbedding = finalEmbedding.map((n) => Number(n));

        if (!Array.isArray(finalEmbedding) || finalEmbedding[0] === undefined) {
            throw new Error(
                "Invalid embedding format: must be an array starting with a number"
            );
        }

        if (finalEmbedding.length !== 384) {
            elizaLogger.warn(
                `Unexpected embedding dimension: ${finalEmbedding.length}`
            );
        }

        return finalEmbedding;
    }

    public async reset(): Promise<void> {
        if (this.model) {
            // Add any cleanup logic here if needed
            this.model = null;
        }
        this.initPromise = null;
        this.initializationLock = false;
    }

    public async forceReinstall(): Promise<void> {
        elizaLogger.info("Force reinstalling BGE embedding model...");
        
        // Reset all state
        this.model = null;
        this.initPromise = null;
        this.initializationLock = false;
        
        try {
            const fs = await import("fs");
            const cacheDir = (await this.getRootPath()) + "/cache/";
            
            // Remove existing cache directory
            if (fs.existsSync(cacheDir)) {
                elizaLogger.debug("Removing existing cache directory:", cacheDir);
                fs.rmSync(cacheDir, { recursive: true, force: true });
                elizaLogger.debug("Cache directory removed successfully");
            }
            
            // Force initialization
            await this.initialize();
            
            elizaLogger.info("BGE embedding model reinstalled successfully");
        } catch (error) {
            elizaLogger.error("Failed to force reinstall BGE model:", error);
            throw error;
        }
    }

    // For testing purposes
    public static resetInstance(): void {
        if (LocalEmbeddingModelManager.instance) {
            LocalEmbeddingModelManager.instance.reset();
            LocalEmbeddingModelManager.instance = null;
        }
    }
}

export default LocalEmbeddingModelManager;
