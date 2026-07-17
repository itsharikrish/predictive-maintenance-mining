export const metadata = {
  title: "Predictive Maintenance Dashboard",
  description: "Live sensor telemetry with ML-based failure-risk prediction",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
