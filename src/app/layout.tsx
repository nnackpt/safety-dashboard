import "./globals.css";
// import Topbar from "@/components/layout/Topbar";
// import Footer from "@/components/layout/Footer";
import LayoutWrapper from "@/components/layout/LayoutWrapper";
// import Navbar from "@/components/layout/์Navbar";
import { CameraProvider } from "@/contexts/CameraContext";
import { ConfigProvider } from "@/contexts/ConfigContext";
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter"
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${inter.className} font-sans antialiased h-screen flex flex-col bg-white overflow-hidden`}>
        {/* <Topbar /> */}
        <ConfigProvider>
          <CameraProvider>
            <LayoutWrapper>
              <main className="flex-1 bg-white flex flex-col min-h-0">
                {children}
              </main>
            </LayoutWrapper>
          </CameraProvider>
        </ConfigProvider>
        {/* <Footer /> */}
      </body>
    </html>
  );
}