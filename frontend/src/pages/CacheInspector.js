import React, { useEffect, useState } from 'react';
import apiClient from '../apiClient';
import './CacheInspector.css';

function CacheInspector() {
    const [cacheData, setCacheData] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchCacheData = async () => {
        try {
            setLoading(true);
            const data = await apiClient.getCacheData();
            setCacheData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCacheData();
    }, []);

    const formatValue = (value) => {
        try {
            const parsedValue = JSON.parse(value);
            return JSON.stringify(parsedValue, null, 2);
        } catch (e) {
            return value;
        }
    };

    const handleDelete = async (key) => {
        try {
            await apiClient.deleteCacheEntry(key);
            fetchCacheData(); // Refresh the cache data
        } catch (err) {
            setError(`Failed to delete entry: ${err.message}`);
        }
    };

    const handleClearAll = async () => {
        try {
            await apiClient.clearAllCache();
            fetchCacheData(); // Refresh the cache data
        } catch (err) {
            setError(`Failed to clear cache: ${err.message}`);
        }
    };

    return (
        <div className="cache-inspector">
            <h2>Cache Inspector</h2>
            <button onClick={handleClearAll} className="clear-all-button">Clear All Cache</button>
            {loading ? (
                <p>Loading...</p>
            ) : error ? (
                <p className="error">Error: {error}</p>
            ) : (
                <table className="cache-table">
                    <thead>
                        <tr>
                            <th>Address</th>
                            <th>Data</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Object.entries(cacheData).map(([key, value]) => (
                            <tr key={key}>
                                <td>{key}</td>
                                <td>
                                    <pre>{formatValue(value)}</pre>
                                </td>
                                <td>
                                    <button onClick={() => handleDelete(key)} className="delete-button">Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}

export default CacheInspector;
