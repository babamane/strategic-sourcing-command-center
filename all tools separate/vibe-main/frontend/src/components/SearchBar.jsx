import React from 'react';
import { Search } from 'lucide-react';
import './SearchBar.css';

const SearchBar = () => {
    return (
        <div className="search-container">
            <div className="search-wrapper">
                <Search className="search-icon" size={20} />
                <input
                    type="text"
                    placeholder="Search for apps, models, and more..."
                    className="search-input"
                />
            </div>
        </div>
    );
};

export default SearchBar;
