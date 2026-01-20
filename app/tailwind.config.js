/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                graphite: {
                    900: '#121416',
                    800: '#1a1c1e',
                    700: '#26292c',
                    600: '#34383d',
                    500: '#4b5259',
                },
                fraud: {
                    approve: '#10b981', // Emerald/Green
                    review: '#f59e0b',  // Amber
                    block: '#dc2626',   // Crimson/Red
                }
            }
        },
    },
    plugins: [],
}
