const express = require("express");
const { createServer } = require("node:http");
const { join } = require("node:path");
const { Server } = require("socket.io");

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: "http://127.0.0.1:8000",
    methods: ["GET", "POST"],
  },
});

const onlineUsers = {};
const userFileMap = {};

app.get("/", (req, res) => {
  res.sendFile(join(__dirname, "index.html"));
});

io.on("connection", (socket) => {
  console.log("A user connected");

  socket.on("joinFile", ({ fileId, username }) => {
    socket.join(fileId);

    if (!onlineUsers[fileId]) {
      onlineUsers[fileId] = [];
    }
    if (!onlineUsers[fileId].includes(username)) {
      onlineUsers[fileId].push(username);
    }

    userFileMap[socket.id] = { fileId, username };
    io.to(fileId).emit("updateCollaborators", onlineUsers[fileId]);
  });

  socket.on("leaveFile", ({ fileId, username }) => {
    socket.leave(fileId);

    if (onlineUsers[fileId]) {
      onlineUsers[fileId] = onlineUsers[fileId].filter(
        (user) => user !== username
      );
      if (onlineUsers[fileId].length === 0) {
        delete onlineUsers[fileId];
      }
    }

    delete userFileMap[socket.id];
    io.to(fileId).emit("updateCollaborators", onlineUsers[fileId]);
  });

  socket.on("textChange", ({ fileId, content, cursor }) => {
    const userData = userFileMap[socket.id];
    if (userData) {
      const { username } = userData;
      socket.to(fileId).emit("textChange", { content, cursor, username });
    }
  });

  socket.on("disconnect", () => {
    console.log("A user disconnected");

    const userData = userFileMap[socket.id];
    if (userData) {
      const { fileId, username } = userData;

      if (onlineUsers[fileId]) {
        onlineUsers[fileId] = onlineUsers[fileId].filter(
          (user) => user !== username
        );
        if (onlineUsers[fileId].length === 0) {
          delete onlineUsers[fileId];
        }
      }

      io.to(fileId).emit("updateCollaborators", onlineUsers[fileId]);
      delete userFileMap[socket.id];
    }
  });
});

server.listen(3000, () => {
  console.log("Server running at http://localhost:3000");
});
