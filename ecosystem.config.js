
module.exports = {
    apps: [
      {
        name: "qiblah-graphql",
        script: "./start_uvicorn.sh",  // Jalankan skrip bash
        exec_mode: "fork",  // Mode fork untuk menjalankan aplikasi di latar belakang
        interpreter: "/bin/bash",  // Gunakan interpreter bash untuk menjalankan skrip
      },
    ],
  };
