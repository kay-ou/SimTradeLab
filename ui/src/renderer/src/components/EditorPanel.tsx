import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import { Button, Space, message, Tag, theme, Tooltip, InputNumber } from "antd";
import { SaveOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import {
  strategiesAPI,
  fetchEditorCompletions,
  CompletionItem,
} from "../services/api";
import { isMac } from "../utils/platform";

interface Props {
  strategyName: string | null;
  isDark?: boolean;
  sourceOverride?: string;
  editorFontSize?: number;
  onEditorFontSizeChange?: (v: number) => void;
}

let _completionRegistered = false;
let _fetchPromise: Promise<CompletionItem[]> | null = null;
let _apiItemsMap: Map<string, CompletionItem> | null = null;

function getApiItems(): Promise<CompletionItem[]> {
  if (!_fetchPromise) {
    _fetchPromise = fetchEditorCompletions()
      .then((items) => {
        _apiItemsMap = new Map(items.map((i) => [i.label, i]));
        return items;
      })
      .catch(() => {
        _fetchPromise = null;
        return [];
      });
  }
  return _fetchPromise;
}

// 静态补全项（无法从 Python API 自动生成）
function buildStaticItems(K: any) {
  return [
    // ── log.*
    {
      label: "log.info",
      kind: K.Function,
      detail: "(msg, *args)",
      insertText: 'log.info("${1:message}")',
      doc: "INFO 日志",
      scopes: ["all"],
    },
    {
      label: "log.warn",
      kind: K.Function,
      detail: "(msg, *args)",
      insertText: 'log.warn("${1:message}")',
      doc: "WARN 日志",
      scopes: ["all"],
    },
    {
      label: "log.error",
      kind: K.Function,
      detail: "(msg, *args)",
      insertText: 'log.error("${1:message}")',
      doc: "ERROR 日志",
      scopes: ["all"],
    },
    {
      label: "log.debug",
      kind: K.Function,
      detail: "(msg, *args)",
      insertText: 'log.debug("${1:message}")',
      doc: "DEBUG 日志",
      scopes: ["all"],
    },
    // ── 生命周期函数定义模板
    {
      label: "def initialize",
      kind: K.Function,
      detail: "(context)",
      insertText:
        "def initialize(context):\n    set_benchmark('${1:000300.SS}')\n    set_slippage(slippage=0.0)\n    set_fixed_slippage(fixedslippage=0.0)\n    set_limit_mode('UNLIMITED')\n    $0",
      doc: "策略初始化，仅执行一次",
      scopes: ["__toplevel__"],
    },
    {
      label: "def handle_data",
      kind: K.Function,
      detail: "(context, data)",
      insertText: "def handle_data(context, data):\n    $0",
      doc: "每个交易周期执行",
      scopes: ["__toplevel__"],
    },
    {
      label: "def before_trading_start",
      kind: K.Function,
      detail: "(context, data)",
      insertText: "def before_trading_start(context, data):\n    $0",
      doc: "每日开盘前执行",
      scopes: ["__toplevel__"],
    },
    {
      label: "def after_trading_end",
      kind: K.Function,
      detail: "(context, data)",
      insertText: "def after_trading_end(context, data):\n    $0",
      doc: "每日收盘后执行",
      scopes: ["__toplevel__"],
    },
    {
      label: "def on_order_response",
      kind: K.Function,
      detail: "(context, order_response)",
      insertText: "def on_order_response(context, order_response):\n    $0",
      doc: "订单响应回调",
      scopes: ["__toplevel__"],
    },
    // ── data[stock].* 属性
    {
      label: "data[stock].close",
      kind: K.Property,
      detail: "-> float",
      insertText: "data[${1:stock}].close",
      doc: "当日收盘价",
      scopes: [
        "handle_data",
        "before_trading_start",
        "after_trading_end",
        "tick_data",
      ],
    },
    {
      label: "data[stock].price",
      kind: K.Property,
      detail: "-> float",
      insertText: "data[${1:stock}].price",
      doc: "当前最新价格",
      scopes: [
        "handle_data",
        "before_trading_start",
        "after_trading_end",
        "tick_data",
      ],
    },
    {
      label: "data[stock].open",
      kind: K.Property,
      detail: "-> float",
      insertText: "data[${1:stock}].open",
      doc: "当日开盘价",
      scopes: [
        "handle_data",
        "before_trading_start",
        "after_trading_end",
        "tick_data",
      ],
    },
    {
      label: "data[stock].high",
      kind: K.Property,
      detail: "-> float",
      insertText: "data[${1:stock}].high",
      doc: "当日最高价",
      scopes: [
        "handle_data",
        "before_trading_start",
        "after_trading_end",
        "tick_data",
      ],
    },
    {
      label: "data[stock].low",
      kind: K.Property,
      detail: "-> float",
      insertText: "data[${1:stock}].low",
      doc: "当日最低价",
      scopes: [
        "handle_data",
        "before_trading_start",
        "after_trading_end",
        "tick_data",
      ],
    },
    {
      label: "data[stock].volume",
      kind: K.Property,
      detail: "-> float",
      insertText: "data[${1:stock}].volume",
      doc: "当日成交量（股）",
      scopes: [
        "handle_data",
        "before_trading_start",
        "after_trading_end",
        "tick_data",
      ],
    },
    // ── 参数变量
    {
      label: "context",
      kind: K.Variable,
      detail: "Context",
      insertText: "context",
      doc: "策略上下文（context.portfolio / context.account / context.current_dt…）",
      scopes: [
        "initialize",
        "handle_data",
        "before_trading_start",
        "after_trading_end",
        "tick_data",
        "on_order_response",
      ],
    },
    {
      label: "data",
      kind: K.Variable,
      detail: "BarData",
      insertText: "data",
      doc: "行情快照（data[stock].close / .open / .volume…）",
      scopes: [
        "handle_data",
        "before_trading_start",
        "after_trading_end",
        "tick_data",
      ],
    },
  ];
}

function registerPtradeCompletions(monaco: any) {
  if (_completionRegistered) return;
  _completionRegistered = true;

  // 立即预加载，不等首次触发
  getApiItems();

  const K = monaco.languages.CompletionItemKind;
  const snip = monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet;
  const kindMap: Record<string, number> = {
    Function: K.Function,
    Property: K.Property,
    Variable: K.Variable,
  };

  const staticItems = buildStaticItems(K);

  // ── context.* 点触发补全数据
  const mk = (label: string, detail: string, doc: string) => ({
    label,
    kind: K.Property,
    detail,
    insertText: label,
    doc,
  });
  const contextProps = [
    mk("portfolio", "-> Portfolio", "投资组合对象"),
    mk("account", "-> Account", "账户信息"),
    mk("current_dt", "-> datetime", "当前日期时间"),
    mk("run_params", "-> RunParams", "运行参数"),
    mk("universe", "-> list", "当前股票池"),
  ];
  const portfolioProps = [
    mk("cash", "-> float", "可用现金"),
    mk("total_value", "-> float", "总资产"),
    mk("portfolio_value", "-> float", "持仓市值"),
    mk("positions", "-> dict[str, Position]", "当前所有持仓"),
    mk("starting_cash", "-> float", "初始资金"),
    mk("returns", "-> float", "累计收益率"),
  ];
  const positionProps = [
    mk("amount", "-> int", "持股数量"),
    mk("avg_cost", "-> float", "持仓均价"),
    mk("value", "-> float", "持仓市值"),
    mk("last_sale_price", "-> float", "最新价格"),
    mk("security", "-> str", "股票代码"),
    mk("side", "-> str", "'long'|'short'"),
  ];
  const runParamsProps = [
    mk("start_date", "-> str", "回测开始日期"),
    mk("end_date", "-> str", "回测结束日期"),
    mk("frequency", "-> str", "'day'|'minute'"),
    mk("benchmark", "-> str", "基准代码"),
    mk("capital_base", "-> float", "初始资金"),
  ];

  const toSuggestions = (props: ReturnType<typeof mk>[]) =>
    props.map(({ label, kind, insertText, detail, doc }) => ({
      label,
      kind,
      detail,
      documentation: doc,
      insertText,
      insertTextRules: snip,
    }));

  const LIFECYCLE = new Set([
    "initialize",
    "before_trading_start",
    "handle_data",
    "after_trading_end",
    "tick_data",
    "on_order_response",
    "on_trade_response",
  ]);

  monaco.languages.registerCompletionItemProvider("python", {
    triggerCharacters: ["."],
    provideCompletionItems: async (model: any, position: any) => {
      const _apiItems = await getApiItems();

      const linePrefix = model
        .getLineContent(position.lineNumber)
        .substring(0, position.column - 1);

      // ── 点触发补全
      if (
        /\bcontext\.portfolio\.positions\b.*\.\w*$/.test(linePrefix) ||
        /\bget_position\(.*\)\.\w*$/.test(linePrefix)
      )
        return { suggestions: toSuggestions(positionProps) };
      if (/\bcontext\.(portfolio|account)\.\w*$/.test(linePrefix))
        return { suggestions: toSuggestions(portfolioProps) };
      if (/\bcontext\.run_params\.\w*$/.test(linePrefix))
        return { suggestions: toSuggestions(runParamsProps) };
      if (/\bcontext\.\w*$/.test(linePrefix))
        return { suggestions: toSuggestions(contextProps) };

      // ── 常规补全：静态 + 动态合并
      // 基于缩进判断当前所在函数（向上找第一个缩进比当前行小的 def）
      const curLine = model.getLineContent(position.lineNumber);
      const curIndent = (curLine.match(/^(\s*)/) ?? ["", ""])[1].length;
      let currentFunc: string | null = null;
      if (curIndent > 0) {
        for (let ln = position.lineNumber - 1; ln >= 1; ln--) {
          const line = model.getLineContent(ln);
          const m = line.match(/^(\s*)def\s+(\w+)\s*\(/);
          if (m && m[1].length < curIndent) {
            currentFunc = m[2];
            break;
          }
        }
      }

      const filterScopes = (scopes: string[]) => {
        if (!currentFunc) return scopes.includes("__toplevel__"); // 顶层：只显示 def 模板
        if (!LIFECYCLE.has(currentFunc)) return scopes.includes("all"); // 用户自定义函数：通用 API
        return scopes.includes("all") || scopes.includes(currentFunc); // 生命周期函数：通用 + 专属
      };

      const allItems = [
        ...staticItems
          .filter(({ scopes }) => filterScopes(scopes))
          .map(({ label, kind, insertText, detail, doc }) => ({
            label,
            kind,
            detail,
            documentation: doc,
            insertText,
            insertTextRules: snip,
          })),
        ..._apiItems
          .filter(({ scopes }) => filterScopes(scopes))
          .map(({ label, kind, insertText, detail, doc }) => ({
            label,
            kind: kindMap[kind] ?? K.Function,
            detail,
            documentation: doc,
            insertText,
            insertTextRules: snip,
          })),
      ];

      return { suggestions: allItems };
    },
  });

  monaco.languages.registerHoverProvider("python", {
    provideHover: async (model: any, position: any) => {
      await getApiItems(); // 确保 map 已建立
      if (!_apiItemsMap) return null;

      const word = model.getWordAtPosition(position);
      if (!word) return null;

      const item = _apiItemsMap.get(word.word);
      if (!item) return null;

      const sig = `${item.label}${item.detail}`;
      const contents: { value: string }[] = [
        { value: ["```python", sig, "```"].join("\n") },
      ];
      if (item.doc) contents.push({ value: item.doc });
      if (!item.scopes.includes("all")) {
        const phases = item.scopes.map((s) => `\`${s}\``).join("  ");
        contents.push({ value: `*可用阶段:* ${phases}` });
      }

      return {
        range: {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        },
        contents,
      };
    },
  });
}

export function EditorPanel({
  strategyName,
  isDark,
  sourceOverride,
  editorFontSize = 13,
  onEditorFontSizeChange,
}: Props) {
  const { token } = theme.useToken();
  const { t } = useTranslation();
  const [source, setSource] = useState("");
  const [saved, setSaved] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!strategyName) return;
    if (sourceOverride !== undefined) {
      setSource(sourceOverride);
      setSaved(true);
      return;
    }
    setLoading(true);
    strategiesAPI
      .get(strategyName)
      .then((s) => {
        setSource(s.source);
        setSaved(true);
      })
      .finally(() => setLoading(false));
  }, [strategyName, sourceOverride]);

  const handleSave = async () => {
    if (!strategyName) return;
    try {
      await strategiesAPI.save(strategyName, source);
      message.success(t("editor.saved"));
      setSaved(true);
    } catch {
      message.error(t("editor.saveFailed"));
    }
  };

  const handleKeyDown = (event: KeyboardEvent) => {
    if ((event.ctrlKey || (isMac && event.metaKey)) && event.key === "s") {
      event.preventDefault();
      handleSave();
    }
  };

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [strategyName, source, handleSave]);

  if (!strategyName) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: token.colorTextSecondary,
        }}
      >
        {t("editor.selectStrategy")}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "4px 8px",
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        <Space>
          <span style={{ fontWeight: 600 }}>{strategyName}</span>
          {!saved && <Tag color="orange">{t("editor.unsaved")}</Tag>}
        </Space>
        <Space>
          {onEditorFontSizeChange && (
            <Space size={4}>
              <span
                style={{
                  fontSize: token.fontSize,
                  color: token.colorTextSecondary,
                }}
              >
                {t("editor.fontSize")}
              </span>
              <InputNumber
                size="small"
                min={10}
                max={24}
                value={editorFontSize}
                onChange={(v) => v && onEditorFontSizeChange(v)}
                style={{ width: 48 }}
              />
            </Space>
          )}
          <Tooltip
            title={t("editor.saveTooltip", { shortcut: isMac ? "⌘" : "Ctrl" })}
          >
            <Button
              size="small"
              icon={<SaveOutlined />}
              onClick={handleSave}
              type={saved ? "default" : "primary"}
            >
              {t("editor.btn.save")}
            </Button>
          </Tooltip>
        </Space>
      </div>
      <Editor
        height="100%"
        defaultLanguage="python"
        value={source}
        loading={loading ? t("editor.loading") : undefined}
        theme={isDark ? "vs-dark" : "vs-light"}
        onMount={(_editor, monaco) => registerPtradeCompletions(monaco)}
        options={{
          fontSize: editorFontSize,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: "on",
          wordBasedSuggestions: "off",
        }}
        onChange={(val) => {
          setSource(val ?? "");
          setSaved(false);
        }}
      />
    </div>
  );
}
