import { useEffect, useRef, useCallback } from "react";
import Message from "./Message";

export default function ChatBox({ messages }) {
 
  return (
    <div >
      {messages.map((msg, index) => (
        <Message
          key={index}
          role={msg.role}
          text={msg.text}
          loading={msg.loading}
          skipTyping={msg.skipTyping || false}
        />
      ))}
    </div>
  );
}