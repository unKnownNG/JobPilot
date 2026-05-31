import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // "standalone" creates a self-contained build that includes only the files
  // needed to run the production server. This is critical for Docker because
  // it means we don't need to copy the entire node_modules folder (~500 MB)
  // into the final image. The standalone output is only ~30 MB.
  output: "standalone",
};

export default nextConfig;
