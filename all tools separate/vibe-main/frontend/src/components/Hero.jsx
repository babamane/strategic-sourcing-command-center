import React from 'react';
import SearchBar from './SearchBar';
import './Hero.css';

const Hero = () => {
    return (
        <section className="hero">
            <div className="hero-content">
                <h1 className="hero-title">
                    Discover <span className="highlight">Intelligent</span> Apps
                </h1>
                <p className="hero-subtitle">
                    Explore a curated collection of AI-powered tools and dashboards designed to accelerate your workflow.
                </p>
                <SearchBar />
            </div>
        </section>
    );
};

export default Hero;
