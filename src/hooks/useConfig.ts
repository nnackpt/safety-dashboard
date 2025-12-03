import { Config, getConfig } from "@/lib/config"
import { useEffect, useState } from "react"

export function useConfig() {
    const [config, setConfig] = useState<Config | null>(null)
    // const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    useEffect(() => {
        getConfig()
            .then((cfg) => {
                setConfig(cfg)
                // setLoading(false)
            })
            .catch((err) => {
                setError(err)
                // setLoading(false)
                // Fallback
                setConfig({
                    API_URL: "http://ath-ma-wd2503:8083/api"
                })
            })
    }, [])

    return { config, error }
}