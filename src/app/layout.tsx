import "./globals.css";
// import Topbar from "@/components/layout/Topbar";
import Footer from "@/components/layout/Footer";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="h-screen flex flex-col bg-[#0B4A82] overflow-hidden">
        {/* <Topbar /> */}
        <main className="flex-1 bg-[#09304F] flex flex-col min-h-0">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}