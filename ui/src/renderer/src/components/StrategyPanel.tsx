import { useEffect, useRef, useState } from "react";
import { Button, Input, Popconfirm, Spin, message, theme } from "antd";
import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import { strategiesAPI } from "../services/api";

interface Props {
  selected: string | null;
  onSelect: (name: string) => void;
  reloadKey?: number;
}

export function StrategyPanel({ selected, onSelect, reloadKey }: Props) {
  const { token } = theme.useToken();
  const [strategies, setStrategies] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [renamingName, setRenamingName] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const renameInputRef = useRef<any>(null);

  const load = async () => {
    setLoading(true);
    try {
      setStrategies(await strategiesAPI.list());
    } catch {
      message.error("加载策略列表失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [reloadKey]);

  useEffect(() => {
    if (renamingName) renameInputRef.current?.select();
  }, [renamingName]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      await strategiesAPI.create(newName.trim());
      setNewName("");
      setCreating(false);
      await load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "创建失败");
    }
  };

  const handleDelete = async (name: string) => {
    await strategiesAPI.delete(name);
    await load();
  };

  const startRename = (name: string) => {
    setRenamingName(name);
    setRenameValue(name);
  };

  const commitRename = async () => {
    const trimmed = renameValue.trim();
    if (!trimmed || trimmed === renamingName) {
      setRenamingName(null);
      return;
    }
    try {
      await strategiesAPI.rename(renamingName!, trimmed);
      if (selected === renamingName) onSelect(trimmed);
      await load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "改名失败");
    } finally {
      setRenamingName(null);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        padding: 8,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 8,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: token.fontSize }}>策略</span>
        <Button
          size="small"
          icon={<PlusOutlined />}
          onClick={() => setCreating(!creating)}
        />
      </div>

      {creating && (
        <Input.Search
          size="small"
          placeholder="策略名称"
          enterButton="创建"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onSearch={handleCreate}
          style={{ marginBottom: 8 }}
        />
      )}

      <Spin spinning={loading} style={{ flex: 1, overflow: "auto" }}>
        {strategies.map((name) => (
          <div
            key={name}
            title={name}
            onClick={() => renamingName !== name && onSelect(name)}
            style={{
              display: "flex",
              alignItems: "center",
              padding: "3px 6px",
              borderRadius: 4,
              cursor: "pointer",
              background:
                name === selected ? token.colorPrimaryBg : "transparent",
              marginBottom: 1,
            }}
            className="strategy-item"
          >
            {renamingName === name ? (
              <Input
                ref={renameInputRef}
                size="small"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={commitRename}
                onPressEnter={commitRename}
                onKeyDown={(e) => e.key === "Escape" && setRenamingName(null)}
                onClick={(e) => e.stopPropagation()}
                style={{ flex: 1 }}
              />
            ) : (
              <>
                <span
                  style={{
                    flex: 1,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    fontSize: token.fontSize,
                  }}
                >
                  {name}
                </span>
                <span
                  className="strategy-actions"
                  style={{ display: "flex", gap: 2, flexShrink: 0 }}
                >
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      startRename(name);
                    }}
                  />
                  <Popconfirm
                    title="确认删除？"
                    onConfirm={() => handleDelete(name)}
                  >
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Popconfirm>
                </span>
              </>
            )}
          </div>
        ))}
      </Spin>

      <style>{`
        .strategy-item .strategy-actions { opacity: 0; }
        .strategy-item:hover .strategy-actions { opacity: 1; }
      `}</style>
    </div>
  );
}
