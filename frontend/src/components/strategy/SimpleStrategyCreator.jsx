import { useState } from 'react';
import { Card, Row, Col, Button, Typography, Alert, message, Tag } from 'antd';
import {
    RocketOutlined,
    SafetyCertificateOutlined,
    ThunderboltOutlined,
    CheckCircleOutlined,
    LineChartOutlined,
    BarChartOutlined,
    RiseOutlined
} from '@ant-design/icons';
import { strategyAPI } from '../../api/strategy';

const { Title, Text, Paragraph } = Typography;

// 3가지 대표 전략 정의
const REPRESENTATIVE_STRATEGIES = {
    proven_conservative: {
        name: '보수적 EMA 크로스오버 전략',
        code: 'proven_conservative',
        icon: <SafetyCertificateOutlined />,
        color: '#52c41a',
        tag: '초보자 추천',
        tagColor: 'green',
        description: '안정적인 수익을 추구하는 전략입니다. EMA 골든크로스와 거래량 확인을 통해 명확한 추세에서만 진입합니다.',
        features: [
            '예상 승률: 60-65%',
            '타임프레임: 4시간봉',
            '레버리지: 5배',
            '손익비 1:2'
        ],
        params: {
            symbol: 'BTCUSDT',
            timeframe: '4h',
            ema_short: 20,
            ema_long: 50,
            rsi_period: 14,
            volume_multiplier: 1.5,
            position_size_percent: 20,
            leverage: 5,
            stop_loss_percent: 4.0,
            take_profit_percent: 8.0
        }
    },
    proven_balanced: {
        name: '균형적 RSI 다이버전스 전략',
        code: 'proven_balanced',
        icon: <BarChartOutlined />,
        color: '#1890ff',
        tag: '균형',
        tagColor: 'blue',
        description: '중간 수준의 위험과 수익을 추구합니다. RSI 다이버전스와 MACD 크로스오버를 함께 확인하여 반전 지점을 포착합니다.',
        features: [
            '예상 승률: 55-60%',
            '타임프레임: 1시간봉',
            '레버리지: 8배',
            '손익비 1:2'
        ],
        params: {
            symbol: 'BTCUSDT',
            timeframe: '1h',
            rsi_period: 14,
            rsi_oversold: 30,
            rsi_overbought: 70,
            macd_fast: 12,
            macd_slow: 26,
            macd_signal: 9,
            position_size_percent: 30,
            leverage: 8,
            stop_loss_percent: 2.0,
            take_profit_percent: 4.0
        }
    },
    proven_aggressive: {
        name: '공격적 모멘텀 브레이크아웃 전략',
        code: 'proven_aggressive',
        icon: <ThunderboltOutlined />,
        color: '#fa541c',
        tag: '고수익',
        tagColor: 'volcano',
        description: '높은 수익 잠재력을 가진 전략입니다. 볼린저 밴드 돌파와 강한 추세(ADX) 및 거래량 급증을 확인하고 진입합니다.',
        features: [
            '예상 승률: 45-50%',
            '타임프레임: 1시간봉',
            '레버리지: 10배',
            '손익비 1:2.7'
        ],
        params: {
            symbol: 'BTCUSDT',
            timeframe: '1h',
            bb_period: 20,
            bb_std: 2.0,
            adx_period: 14,
            adx_threshold: 25,
            volume_multiplier: 2.0,
            position_size_percent: 40,
            leverage: 10,
            stop_loss_percent: 1.5,
            take_profit_percent: 4.0
        }
    }
};

export default function SimpleStrategyCreator({ onStrategyCreated }) {
    const [selectedStrategy, setSelectedStrategy] = useState(null);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const handleSelectStrategy = async (strategyKey) => {
        const strategy = REPRESENTATIVE_STRATEGIES[strategyKey];

        setLoading(true);
        try {
            const strategyData = {
                name: strategy.name,
                description: strategy.description,
                type: strategy.code,
                code: strategy.code,
                symbol: strategy.params.symbol,
                timeframe: strategy.params.timeframe,
                parameters: strategy.params
            };

            await strategyAPI.createStrategy(strategyData);
            message.success(`'${strategy.name}' 전략이 등록되었습니다.`);
            setSelectedStrategy(strategyKey);
            setSuccess(true);

            if (onStrategyCreated) {
                onStrategyCreated();
            }

        } catch (error) {
            console.error('Strategy creation error:', error);
            message.error(error.response?.data?.detail || '전략 등록에 실패했습니다');
        } finally {
            setLoading(false);
        }
    };

    // 성공 화면
    if (success) {
        const strategy = REPRESENTATIVE_STRATEGIES[selectedStrategy];
        return (
            <Card
                style={{
                    maxWidth: 800,
                    margin: '0 auto',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                    borderRadius: 16,
                    textAlign: 'center',
                    padding: '40px 20px'
                }}
            >
                <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 24 }} />
                <Title level={2}>전략 등록 완료!</Title>
                <Paragraph type="secondary" style={{ fontSize: 16 }}>
                    <strong>{strategy.name}</strong>이(가) 성공적으로 등록되었습니다.
                </Paragraph>
                <Row gutter={16} justify="center" style={{ marginTop: 32 }}>
                    <Col>
                        <Button
                            size="large"
                            onClick={() => {
                                setSuccess(false);
                                setSelectedStrategy(null);
                            }}
                        >
                            다른 전략 등록
                        </Button>
                    </Col>
                    <Col>
                        <Button
                            type="primary"
                            size="large"
                            onClick={() => window.location.href = '/strategy'}
                        >
                            전략 관리로 이동
                        </Button>
                    </Col>
                </Row>
            </Card>
        );
    }

    return (
        <Card
            style={{
                maxWidth: 1000,
                margin: '0 auto',
                boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                borderRadius: 16
            }}
        >
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
                <Title level={2} style={{ marginBottom: 8 }}>
                    <RocketOutlined /> 전략 선택
                </Title>
                <Text type="secondary" style={{ fontSize: 16 }}>
                    검증된 3가지 대표 전략 중 하나를 선택하세요
                </Text>
            </div>

            <Alert
                message="초보자 팁"
                description="처음 시작하신다면 '보수적 EMA 크로스오버 전략'을 추천드립니다. 가장 안정적이고 이해하기 쉬운 전략입니다."
                type="info"
                showIcon
                style={{ marginBottom: 24, background: '#f5f5f7', border: '1px solid #d2d2d7' }}
            />

            <Row gutter={[16, 16]}>
                {Object.entries(REPRESENTATIVE_STRATEGIES).map(([key, strategy]) => (
                    <Col xs={24} md={8} key={key}>
                        <Card
                            hoverable
                            onClick={() => !loading && handleSelectStrategy(key)}
                            loading={loading && selectedStrategy === key}
                            style={{
                                height: '100%',
                                borderRadius: 12,
                                border: `2px solid ${strategy.color}20`,
                                transition: 'all 0.3s ease'
                            }}
                            bodyStyle={{ padding: 20 }}
                        >
                            <div style={{ textAlign: 'center' }}>
                                {/* 아이콘 */}
                                <div style={{
                                    width: 64,
                                    height: 64,
                                    borderRadius: '50%',
                                    background: `${strategy.color}15`,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    margin: '0 auto 16px',
                                    fontSize: 28,
                                    color: strategy.color
                                }}>
                                    {strategy.icon}
                                </div>

                                {/* 태그 */}
                                <Tag color={strategy.tagColor} style={{ marginBottom: 12 }}>
                                    {strategy.tag}
                                </Tag>

                                {/* 이름 */}
                                <Title level={4} style={{ marginBottom: 8, color: '#1d1d1f' }}>
                                    {strategy.name}
                                </Title>

                                {/* 설명 */}
                                <Paragraph
                                    type="secondary"
                                    style={{
                                        fontSize: 13,
                                        marginBottom: 16,
                                        minHeight: 60
                                    }}
                                >
                                    {strategy.description}
                                </Paragraph>

                                {/* 특징 */}
                                <div style={{
                                    background: '#f5f5f7',
                                    borderRadius: 8,
                                    padding: 12,
                                    textAlign: 'left'
                                }}>
                                    {strategy.features.map((feature, idx) => (
                                        <div key={idx} style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            marginBottom: idx < strategy.features.length - 1 ? 6 : 0,
                                            fontSize: 12,
                                            color: '#595959'
                                        }}>
                                            <RiseOutlined style={{ marginRight: 8, color: strategy.color }} />
                                            {feature}
                                        </div>
                                    ))}
                                </div>

                                {/* 버튼 */}
                                <Button
                                    type="primary"
                                    block
                                    size="large"
                                    style={{
                                        marginTop: 16,
                                        background: strategy.color,
                                        borderColor: strategy.color
                                    }}
                                    loading={loading && selectedStrategy === key}
                                >
                                    이 전략 선택
                                </Button>
                            </div>
                        </Card>
                    </Col>
                ))}
            </Row>

            <div style={{
                marginTop: 32,
                padding: 16,
                background: '#fafafa',
                borderRadius: 8,
                textAlign: 'center'
            }}>
                <LineChartOutlined style={{ fontSize: 20, color: '#8c8c8c', marginRight: 8 }} />
                <Text type="secondary">
                    전략 선택 후 '전략 관리' 페이지에서 상세 설정을 변경할 수 있습니다.
                </Text>
            </div>
        </Card>
    );
}
