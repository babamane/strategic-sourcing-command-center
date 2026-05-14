import React from 'react';
import { ExternalLink, Heart } from 'lucide-react';
import './AppCard.css';

const AppCard = ({ title, description, author, image, tags }) => {
    return (
        <div className="app-card">
            <div className="card-image-wrapper">
                <img src={image} alt={title} className="card-image" />
                <div className="card-overlay">
                    <button className="card-action-btn">
                        <ExternalLink size={18} />
                    </button>
                </div>
            </div>
            <div className="card-content">
                <div className="card-header">
                    <h3 className="card-title">{title}</h3>
                    <button className="like-btn">
                        <Heart size={16} />
                    </button>
                </div>
                <p className="card-author">by {author}</p>
                <p className="card-description">{description}</p>
                <div className="card-tags">
                    {tags.map((tag, index) => (
                        <span key={index} className="tag">{tag}</span>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default AppCard;
