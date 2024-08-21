module.exports = {
    apps: [
      {
        name: "qiblah-graphql",    // Name of the app in PM2
        script: "app.js",          // Node.js file to execute
        exec_mode: "cluster",      // Cluster mode for multi-node processes
        instances: 3,              // Number of instances (3 nodes)
        interpreter: "node",       // Node.js interpreter to use
        watch: true,               // Enable watch mode (optional, for development)
        autorestart: true,         // Auto-restart if the app crashes
        max_memory_restart: "1G",  // Restart if memory usage exceeds 1GB
      }
    ]
  };