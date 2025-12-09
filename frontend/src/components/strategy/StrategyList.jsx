import { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, Switch, Popconfirm, message } from 'antd';
import {
    UnorderedListOutlined,
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    PlayCircleOutlined,
    PauseCircleOutlined,
    ReloadOutlined,
} from '@ant-design/icons';
import { useStrategies } from '../../context/StrategyContext';

export default function StrategyList({ onEdit, onNew, onStrategiesLoaded }) {
    const {
        strategies: globalStrategies,
        loading: globalLoading,
        loadStrategies,
        deleteStrategy,
        toggleStrategy,
        refreshStrategies
    } = useStrategies();

    // 테이블용 포맷된 전략 데이터
    const [formattedStrategies, setFormattedStrategies] = useState([]);

    // 전역 상태가 변경되면 포맷된 데이터 업데이트
    useEffect(() => {
        const formatted = globalStrategies.map(s => ({
            id: s.id,
            name: s.name,
            description: s.description,
            type: s.type || 'TREND_FOLLOWING',
            status: s.is_active ? 'ACTIVE' : 'INACTIVE',
            symbols: [s.symbol],
            timeframe: s.timeframe,
            winRate: s.parameters?.win_rate || 0,
            totalTrades: s.parameters?.total_trades || 0,
            profit: s.parameters?.profit || 0,
            parameters: s.parameters,
        }));

        setFormattedStrategies(formatted);

        // 부모 컴포넌트에 전략 목록 전달
        if (onStrategiesLoaded) {
            onStrategiesLoaded(formatted);
        }
    }, [globalStrategies, onStrategiesLoaded]);

    const handleToggleStatus = async (strategy) => {
        try {
            const newActiveStatus = await toggleStrategy(strategy.id);
            message.success(`전략이 ${newActiveStatus ? '활성화' : '비활성화'}되었습니다`);
        } catch (error) {
            console.error('[StrategyList] Error toggling status:', error);
            message.error('전략 상태 변경에 실패했습니다');
        }
    };

    const handleDelete = async (strategyId) => {
        try {
            await deleteStrategy(strategyId);
            message.success('전략이 삭제되었습니다');
        } catch (error) {
            console.error('[StrategyList] Error deleting strategy:', error);
            message.error('전략 삭제에 실패했습니다');
        }
    };

    const getStatusTag = (status) => {
        const statusConfig = {
            ACTIVE: { color: 'success', text: '활성' },
            INACTIVE: { color: 'default', text: '비활성' },
            TESTING: { color: 'processing', text: '테스트' },
            ERROR: { color: 'error', text: '오류' },
        };

        const config = statusConfig[status] || statusConfig.INACTIVE;
        return <Tag color={config.color}>{config.text}</Tag>;
    };

    const getTypeTag = (type) => {
        const typeConfig = {
            TREND_FOLLOWING: { color: 'blue', text: '추세 추종' },
            MEAN_REVERSION: { color: 'purple', text: '평균 회귀' },
            BREAKOUT: { color: 'orange', text: '돌파' },
            GRID: { color: 'cyan', text: '그리드' },
            SCALPING: { color: 'magenta', text: '스캘핑' },
        };

        const config = typeConfig[type] || { color: 'default', text: type };
        return <Tag color={config.color}>{config.text}</Tag>;
    };

    const columns = [
        {
            title: '전략명',
            dataIndex: 'name',
            key: 'name',
            width: 200,
            render: (name, record) => (
                <div style={{ cursor: 'pointer' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '15px', color: '#1d1d1f' }}>{name}</div>
                    <div style={{ fontSize: 12, color: '#1890ff', marginTop: '4px' }}>
                        👉 클릭하여 상세 설명 보기
                    </div>
                </div>
            ),
        },
        {
            title: '유형',
            dataIndex: 'type',
            key: 'type',
            width: 120,
            render: getTypeTag,
        },
        {
            title: '상태',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: getStatusTag,
        },
        {
            title: '심볼',
            dataIndex: 'symbols',
            key: 'symbols',
            width: 180,
            render: (symbols) => (
                <div>
                    {symbols.map((symbol, index) => (
                        <Tag key={index} style={{ marginBottom: 4 }}>
                            {symbol}
                        </Tag>
                    ))}
                </div>
            ),
        },
        {
            title: '타임프레임',
            dataIndex: 'timeframe',
            key: 'timeframe',
            width: 100,
            align: 'center',
        },

        {
            title: '작업',
            key: 'actions',
            width: 200,
            fixed: 'right',
            render: (_, record) => (
                <Space size="small">
                    <Switch
                        checked={record.status === 'ACTIVE'}
                        onChange={() => handleToggleStatus(record)}
                        checkedChildren={<PlayCircleOutlined />}
                        unCheckedChildren={<PauseCircleOutlined />}
                        size="small"
                    />
                    <Button
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => onEdit && onEdit(record)}
                        size="small"
                    >
                        편집
                    </Button>
                    <Popconfirm
                        title="전략 삭제"
                        description="정말로 이 전략을 삭제하시겠습니까?"
                        onConfirm={() => handleDelete(record.id)}
                        okText="삭제"
                        cancelText="취소"
                        okButtonProps={{ danger: true }}
                    >
                        <Button
                            type="link"
                            danger
                            icon={<DeleteOutlined />}
                            size="small"
                        >
                            삭제
                        </Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <Card
            title={
                <span>
                    <UnorderedListOutlined style={{ marginRight: 8 }} />
                    전략 목록
                </span>
            }
            extra={
                <Space>
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={refreshStrategies}
                        loading={globalLoading}
                        size="small"
                    >
                        새로고침
                    </Button>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => onNew && onNew()}
                    >
                        새 전략
                    </Button>
                </Space>
            }
        >
            <Table
                columns={columns}
                dataSource={formattedStrategies}
                rowKey="id"
                loading={globalLoading}
                pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `총 ${total}개`,
                }}
                scroll={{ x: 1200 }}
                expandable={{
                    expandedRowRender: (record) => (
                        <div style={{ padding: '20px', background: '#f8f9fa', borderRadius: '8px' }}>
                            <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center' }}>
                                <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff', marginRight: '8px' }}>
                                    📖 전략 상세 가이드
                                </span>
                                <Tag color="blue">초보자 추천</Tag>
                            </div>
                            <div style={{
                                whiteSpace: 'pre-wrap',
                                lineHeight: '1.8',
                                color: '#2c3e50',
                                fontSize: '14px',
                                background: '#ffffff',
                                padding: '24px',
                                borderRadius: '12px',
                                border: '1px solid #e8e8e8',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.02)'
                            }}>
                                {record.description || '상세 설명이 없습니다.'}
                            </div>
                        </div>
                    ),
                    rowExpandable: (record) => true,
                    expandRowByClick: true, // 행 클릭 시 확장
                }}
            />
        </Card>
    );
}
