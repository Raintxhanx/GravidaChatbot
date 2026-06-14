import './style.css';
import { LandingPage } from './pages/home.js';
import { LoginPage } from './pages/login.js';
import { RegisterPage } from './pages/register.js';
import { DashboardPage } from './pages/dashboard.js';
import { HistoryPage } from './pages/history.js';
import { SessionPage } from './pages/session.js'; // 1. Import SessionPage

// Mapping URL ke komponen halaman (Mendukung placeholder :id)
const routes = {
    '/': LandingPage,
    '/login': LoginPage,
    '/register': RegisterPage,
    '/dashboard': DashboardPage,
    '/history': HistoryPage,
    '/session/:id': SessionPage
};

// Fungsi untuk mencocokkan path dinamis menggunakan Regex sederhana
const matchRoute = (currentPath) => {
    for (const route in routes) {
        // Mengubah '/session/:id' menjadi regex ^/session/([^/]+)$
        const routeRegex = new RegExp('^' + route.replace(/\/:[^\s/]+/g, '/([^/]+)') + '$');
        const match = currentPath.match(routeRegex);
        
        if (match) {
            return {
                view: routes[route],
                params: match[1] || null // Mengambil ID dari URL jika ada
            };
        }
    }
    return { view: LandingPage, params: null };
};

const updateNavbar = (path) => {
    const globalNav = document.getElementById('global-nav');
    if (!globalNav) return;

    const token = localStorage.getItem('access_token');
    const isRoot = path === '/';

    if (token) {
        globalNav.innerHTML = isRoot ? `
            <a href="#contact" class="px-4 py-2 rounded-[12px] bg-[#FBC3C1]/40 text-gray-700 text-sm font-medium">Contact</a>
            <a href="#faq" class="px-4 py-2 rounded-[12px] bg-[#FBC3C1]/40 text-gray-700 text-sm font-medium">FAQ</a>
            <a href="/dashboard" data-link class="px-5 py-2 rounded-[12px] bg-gradient-to-r from-[#FE81D4] to-[#f472b6] text-white text-sm font-semibold shadow-md">Dashboard</a>
        ` : `
            <a href="/dashboard" data-link class="px-5 py-2 rounded-[12px] bg-gradient-to-r from-[#FE81D4] to-[#f472b6] text-white text-sm font-semibold shadow-md">Dashboard</a>
        `;
    } else {
        globalNav.innerHTML = isRoot ? `
            <a href="#contact" class="px-4 py-2 rounded-[12px] bg-[#FBC3C1]/40 text-gray-700 text-sm font-medium">Contact</a>
            <a href="#faq" class="px-4 py-2 rounded-[12px] bg-[#FBC3C1]/40 text-gray-700 text-sm font-medium">FAQ</a>
            <a href="/login" data-link class="px-5 py-2 rounded-[12px] bg-gradient-to-r from-[#FE81D4] to-[#f472b6] text-white text-sm font-semibold shadow-md">Login</a>
        ` : `
            <a href="/login" data-link class="px-5 py-2 rounded-[12px] bg-gradient-to-r from-[#FE81D4] to-[#f472b6] text-white text-sm font-semibold shadow-md">Login</a>
        `;
    }
};

const router = () => {
    const path = window.location.pathname;
    const { view, params } = matchRoute(path); // Gunakan fungsi pencocok rute dinamis

    updateNavbar(path);

    const appRoot = document.getElementById('app-root');
    if (appRoot) {
        // Anda bisa mengoper params ke fungsi render jika dibutuhkan di masa depan
        const htmlContent = typeof view.render === 'function' ? view.render() : view();
        appRoot.innerHTML = htmlContent;

        if (typeof view.afterrender === 'function') {
            view.afterrender(params); // Mengoper parameter ID ke lifecycle afterrender
        }
    }
};

export const navigateTo = (url) => {
    window.history.pushState(null, null, url);
    router();
    window.scrollTo(0, 0); 
};

// Global Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    document.body.addEventListener('click', (e) => {
        const targetLink = e.target.closest('[data-link]');
        if (targetLink) {
            e.preventDefault();
            navigateTo(targetLink.getAttribute('href'));
        }
    });

    router();

    // Animasi Header
    const header = document.getElementById('main-header');
    if (header) {
        let lastScrollY = window.scrollY;
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            if (currentScrollY > lastScrollY && currentScrollY > 100) {
                header.classList.add('-translate-y-[150%]');
            } else {
                header.classList.remove('-translate-y-[150%]');
            }
            lastScrollY = currentScrollY;
        });
    }
});

window.addEventListener('popstate', router);