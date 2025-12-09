/**
 * 전략 관리 Context
 * 전략 목록 상태를 전역으로 관리하여 전략관리 페이지와 트레이딩 페이지 간의 연동을 처리
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { strategyAPI } from '../api/strategy';

const StrategyContext = createContext();

export function StrategyProvider({ children }) {
    const [strategies, setStrategies] = useState([]);
    const [loading, setLoading] = useState(false);
    const [lastUpdated, setLastUpdated] = useState(null);

    /**
     * 전략 목록 로드 (백엔드에서 가져오기)
     */
    const loadStrategies = useCallback(async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                console.log('[StrategyContext] No token, skipping strategy load');
                setStrategies([]);
                setLoading(false);
                return [];
            }

            const data = await strategyAPI.getAIStrategies();
            const allStrategies = data.strategies || [];

            setStrategies(allStrategies);
            setLastUpdated(Date.now());
            console.log(`[StrategyContext] Loaded ${allStrategies.length} strategies`);

            return allStrategies;
        } catch (error) {
            console.error('[StrategyContext] Error loading strategies:', error);
            return [];
        } finally {
            setLoading(false);
        }
    }, []);

    /**
     * 활성화된 전략만 가져오기 (트레이딩 페이지용)
     */
    const getActiveStrategies = useCallback(() => {
        return strategies.filter(s => s.is_active === true);
    }, [strategies]);

    /**
     * 전략 삭제 후 목록 새로고침
     */
    const deleteStrategy = useCallback(async (strategyId) => {
        try {
            const token = localStorage.getItem('token');
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            const response = await fetch(`${API_BASE_URL}/ai/strategies/${strategyId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to delete strategy');
            }

            // 즉시 로컬 상태에서 제거
            setStrategies(prev => prev.filter(s => s.id !== strategyId));
            setLastUpdated(Date.now());

            console.log(`[StrategyContext] Strategy ${strategyId} deleted`);
            return true;
        } catch (error) {
            console.error('[StrategyContext] Error deleting strategy:', error);
            throw error;
        }
    }, []);

    /**
     * 전략 활성/비활성 토글 후 목록 업데이트
     */
    const toggleStrategy = useCallback(async (strategyId) => {
        try {
            const token = localStorage.getItem('token');
            const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            const response = await fetch(`${API_BASE_URL}/strategy/${strategyId}/toggle`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to toggle strategy status');
            }

            const data = await response.json();
            const newActiveStatus = data.is_active;

            // 즉시 로컬 상태 업데이트
            setStrategies(prev => prev.map(s =>
                s.id === strategyId ? { ...s, is_active: newActiveStatus } : s
            ));
            setLastUpdated(Date.now());

            console.log(`[StrategyContext] Strategy ${strategyId} toggled to ${newActiveStatus ? 'active' : 'inactive'}`);
            return newActiveStatus;
        } catch (error) {
            console.error('[StrategyContext] Error toggling strategy:', error);
            throw error;
        }
    }, []);

    /**
     * 전략 목록 강제 새로고침 트리거
     */
    const refreshStrategies = useCallback(() => {
        setLastUpdated(Date.now());
        return loadStrategies();
    }, [loadStrategies]);

    // 초기 로드
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            loadStrategies();
        }
    }, [loadStrategies]);

    const value = {
        strategies,
        loading,
        lastUpdated,
        loadStrategies,
        getActiveStrategies,
        deleteStrategy,
        toggleStrategy,
        refreshStrategies,
    };

    return (
        <StrategyContext.Provider value={value}>
            {children}
        </StrategyContext.Provider>
    );
}

export function useStrategies() {
    const context = useContext(StrategyContext);
    if (!context) {
        throw new Error('useStrategies must be used within a StrategyProvider');
    }
    return context;
}

export default StrategyContext;
