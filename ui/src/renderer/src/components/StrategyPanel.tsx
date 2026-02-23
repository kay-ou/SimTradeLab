import { useEffect, useState } from "react";
import { Button, List, Input, Popconfirm, message, Spin } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { strategiesAPI } from "../services/api";

interface Props {
  selected: string | null;
  onSelect: (name: string) => void;
  reloadKey?: number;
}

export function StrategyPanel({ selected, onSelect, reloadKey }: Props) {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

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

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      await strategiesAPI.create(newName.trim());
      message.success(`策略 "${newName}" 已创建`);
      setNewName("");
      setCreating(false);
      await load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "创建失败");
    }
  };

  const handleDelete = async (name: string) => {
    await strategiesAPI.delete(name);
    message.success(`策略 "${name}" 已删除`);
    await load();
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
        <span style={{ fontWeight: 600, fontSize: 13 }}>策略</span>
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
      <Spin spinning={loading} style={{ flex: 1 }}>
        <List
          size="small"
          dataSource={strategies}
          renderItem={(name) => (
            <List.Item
              style={{
                cursor: "pointer",
                background: name === selected ? "#e6f4ff" : "transparent",
                padding: "4px 8px",
                borderRadius: 4,
              }}
              onClick={() => onSelect(name)}
              actions={[
                <Popconfirm
                  key="del"
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
                </Popconfirm>,
              ]}
            >
              {name}
            </List.Item>
          )}
        />
      </Spin>
    </div>
  );
}
