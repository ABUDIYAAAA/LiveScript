const express = require("express");
const { createServer } = require("node:http");
const { join } = require("node:path");
const { Server } = require("socket.io");

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: "https://livescript-rza9.onrender.com",
    methods: ["GET", "POST"],
  },
});

const onlineUsers = {};
const userFileMap = {};
const fileCursorPositions = {};

// Remove serving of index.html
// app.get("/", (req, res) => {
//   res.sendFile(join(__dirname, "index.html"));
// });

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

    // Initialize cursor position
    if (!fileCursorPositions[fileId]) {
      fileCursorPositions[fileId] = {};
    }
    fileCursorPositions[fileId][username] = { line: 0, ch: 0 };

    // Emit existing cursor positions to the new user
    socket.emit("updateCursorPositions", fileCursorPositions[fileId]);

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

    // Remove cursor position when user leaves
    if (fileCursorPositions[fileId] && fileCursorPositions[fileId][username]) {
      delete fileCursorPositions[fileId][username];
    }

    // Notify other users to remove the cursor
    socket.to(fileId).emit("removeCursor", username);

    delete userFileMap[socket.id];
    io.to(fileId).emit("updateCollaborators", onlineUsers[fileId]);
  });

  socket.on("textChange", ({ fileId, content, cursor }) => {
    const userData = userFileMap[socket.id];
    if (userData) {
      const { username } = userData;

      // Update cursor position in our server-side storage
      if (fileCursorPositions[fileId]) {
        fileCursorPositions[fileId][username] = cursor;
      }

      socket.to(fileId).emit("textChange", { content, cursor, username });
    }
  });

  socket.on("cursorActivity", ({ fileId, cursor, username }) => {
    // Update cursor position
    if (fileCursorPositions[fileId]) {
      fileCursorPositions[fileId][username] = cursor;
    }

    // Broadcast cursor position to other users
    socket.to(fileId).emit("updateCursor", { username, cursor });
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

      // Remove cursor position when user disconnects
      if (
        fileCursorPositions[fileId] &&
        fileCursorPositions[fileId][username]
      ) {
        delete fileCursorPositions[fileId][username];
      }

      // Notify other users to remove the cursor
      socket.to(fileId).emit("removeCursor", username);

      io.to(fileId).emit("updateCollaborators", onlineUsers[fileId]);
      delete userFileMap[socket.id];
    }
  });
});

server.listen(3000, () => {
  const host =
    server.address().address === "::" ? "localhost" : server.address().address;
  const port = server.address().port;
  console.log(`Server running at http://${host}:${port}`);
});
