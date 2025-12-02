"use client";

import { createContext, useContext, useEffect, useState } from 'react';

interface Config {
  API_URL: string;
}

interface ConfigContextType {
  config: Config | null;
  loading: boolean;
}

const ConfigContext = createContext<ConfigContextType>({
  config: null,
  loading: true
});

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/config.json')
      .then(res => res.json())
      .then(data => {
        setConfig(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load config:', err);
        setLoading(false);
      });
  }, []);

  return (
    <ConfigContext.Provider value={{ config, loading }}>
      {children}
    </ConfigContext.Provider>
  );
}

export const useConfig = () => useContext(ConfigContext);