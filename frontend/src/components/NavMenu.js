import React from 'react';
import { Link } from 'react-router-dom';
import './NavMenu.css';

function NavMenu() {
  return (
    <nav className="nav-menu">
      <div className="nav-content">
        <div className="logo">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="#ffffff" d="M21 14.5V10c0-3.9-3.1-7-7-7s-7 3.1-7 7v4.5c-1.2 1.1-2 2.7-2 4.5 0 3.3 2.7 6 6 6s6-2.7 6-6c0-1.8-0.8-3.4-2-4.5zM14 20h-4v-2h4v2zm1-4H9v-2h6v2zm0-4H9v-2h6v2z"/>
          </svg>
          <span>PostGen</span>
        </div>
        <div className="menu-items">
          <Link to="/">Home</Link>
          <Link to="/cache-inspector">Cache Inspector</Link>
        </div>
      </div>
    </nav>
  );
}

export default NavMenu;
