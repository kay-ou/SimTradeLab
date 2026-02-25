import { useEffect, useRef, useState } from "react";
import { theme, Badge } from "antd";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<"all" | "errors">("all");
  const bottomRef = useRef<HTMLDivElement>(null);

  const errorLogs = logs.filter((l) => l.level === "ERROR");
  const displayLogs = activeTab === "all" ? logs : errorLogs;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayLogs.length]);

  const colors = isDark ? DARK_COLORS : LIGHT_COLORS;
  const tsColor = isDark ? "#6a9955" : "#8c959f";
  const emptyColor = isDark ? "#555" : "#aaa";

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: token.colorBgContainer,
        borderTop: `1px solid ${token.colorBorderSecondary}`,
      }}
    >
      {/* Tab bar */}
      <div
        style={{
          display: "flex",
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          flexShrink: 0,
          padding: "0 4px",
        }}
      >
        {(["all", "errors"] as const).map((key) => (
          <div
            key={key}
            onClick={() => setActiveTab(key)}
            style={{
              padding: "4px 10px",
              cursor: "pointer",
              fontSize: token.fontSize,
              borderBottom:
                activeTab === key
                  ? `2px solid ${token.colorPrimary}`
                  : "2px solid transparent",
              color:
                activeTab === key
                  ? token.colorPrimary
                  : token.colorTextSecondary,
              marginBottom: -1,
              userSelect: "none",
            }}
          >
            {key === "all" ? (
              t("log.tab.all")
            ) : (
              <span
                style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
              >
                {t("log.tab.errors")}
                <Badge count={errorLogs.length} size="small" />
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Content */}
      <div
        style={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          padding: "4px 12px 8px",
          fontFamily: "monospace",
          fontSize: token.fontSize,
        }}
      >
        {displayLogs.length === 0 && (
          <span style={{ color: emptyColor }}>
            {activeTab === "all" ? t("log.empty") : t("log.noErrors")}
          </span>
        )}
        {displayLogs.map((log, i) => (
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
    </div>
  );
}
