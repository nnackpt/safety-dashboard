let cachedConfig: Config | null = null

export interface Config {
    API_URL: string
}

export async function getConfig(): Promise<Config> {
    if (cachedConfig) return cachedConfig

    try {
        const response = await fetch("/config.json", {
            cache: "no-store"
        })

        if (!response.ok) {
            throw new Error("Failed to load config")
        }

        cachedConfig = await response.json()
        return cachedConfig!
    } catch (err) {
        console.error("Failed to load config", err)
        return {
            API_URL: "http://ath-ma-wd2503:8083/api"
        }
    }
}

export function clearConfigCache() {
    cachedConfig = null
}