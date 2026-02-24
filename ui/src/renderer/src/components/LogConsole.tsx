import { useEffect, useRef } from "react";
import { theme } from "antd";

export type LogMessage = {
  level: string;
  msg: string;
  ts: number;
  date?: string;
};

const DARK_COLORS: Record<string, string> = {
  INFO: "#4fc3f7",
  WARNING: "#ffb74d",
  ERROR: "#ef9a9a",
  DEBUG: "#90a4ae",
  SYSTEM: "#81c784",
};
const LIGHT_COLORS: Record<string, string> = {
  INFO: "#0969da",
  WARNING: "#9a6700",
  ERROR: "#cf222e",
  DEBUG: "#6e7781",
  SYSTEM: "#1a7f37",
};

interface Props {
  logs: LogMessage[];
  isDark: boolean;
}

export function LogConsole({ logs, isDark }: Props) {
  const { token } = theme.useToken();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  const colors = isDark ? DARK_COLORS : LIGHT_COLORS;
  const tsColor = isDark ? "#6a9955" : "#8c959f";
  const emptyColor = isDark ? "#555" : "#aaa";

  return (
    <div
      style={{
        height: "100%",
        overflowY: "auto",
        background: token.colorBgContainer,
        padding: "8px 12px",
        fontFamily: "monospace",
        fontSize: 12,
        borderTop: `1px solid ${token.colorBorderSecondary}`,
      }}
    >
      {logs.length === 0 && (
        <span style={{ color: emptyColor }}>等待日志输出...</span>
      )}
      {logs.map((log, i) => (
        <div
          key={i}
          style={{
            color: colors[log.level] ?? token.colorText,
            lineHeight: 1.5,
            marginBottom: 1,
          }}
        >
          {log.date && (
            <span style={{ color: tsColor, marginRight: 8 }}>{log.date}</span>
          )}
          {log.msg}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
