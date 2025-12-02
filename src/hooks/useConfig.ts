import { useEffect, useState } from "react"

interface Config {
    API_URL: string
}

export const useConfig = () => {
    const [config, setConfig] = useState<Config | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/config/json')
            .then(res => res.json())
            .then(data => {
                setConfig(data)
                setLoading(false)
            })
            .catch(err => {
                console.error("Failed to load config:", err)
                setLoading(false)
            })
    }, [])

    return { config, loading }
}