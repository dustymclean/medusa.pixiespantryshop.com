import React, { useState, useMemo } from 'react';
import { Search, Filter, ShoppingCart, Info, Check, Youtube, Instagram, MessageSquare, Mail } from 'lucide-react';

// --- MOCK DATA ---
const MOCK_PRODUCTS = [
 {
   id: 'prod_1',
   name: 'Obsidian Ultrasonic Diffuser',
   category: 'Devices',
   brand: 'AromaTech',
   price: 129.99,
   inStock: 14,
   badge: 'Bestseller',
   description: 'A heavy, cold-rolled steel and obsidian glass diffuser. Built like a tank, runs completely silent.',
   imageUrl: '/api/placeholder/400/400'
 },
 {
   id: 'prod_2',
   name: 'Midnight Lavender Extract',
   category: 'Botanicals',
   brand: 'Pixie Reserve',
   price: 34.00,
   inStock: 42,
   badge: 'Organic',
   description: 'Pure, uncut lavender. None of that synthetic fragrance oil garbage. Sourced directly from high-altitude farms.',
   imageUrl: '/api/placeholder/400/400'
 },
 {
   id: 'prod_3',
   name: 'Titanium Travel Vaporizer',
   category: 'Devices',
   brand: 'VapeDynamics',
   price: 249.00,
   inStock: 5,
   badge: 'Low Stock',
   description: 'Machined from aerospace-grade titanium. Heats up in 12 seconds and actually holds a charge for a full weekend.',
   imageUrl: '/api/placeholder/400/400'
 },
 {
   id: 'prod_4',
   name: 'Eucalyptus & Mint Clarity Blend',
   category: 'Botanicals',
   brand: 'Pixie Reserve',
   price: 28.50,
   inStock: 0,
   badge: 'Sold Out',
   description: 'Sharp, clean, and cuts right through brain fog. We tested 14 different mint ratios before settling on this one.',
   imageUrl: '/api/placeholder/400/400'
 },
 {
   id: 'prod_5',
   name: 'Desktop Glass Nebulizer',
   category: 'Devices',
   brand: 'AromaTech',
   price: 185.00,
   inStock: 8,
   badge: 'Premium',
   description: 'Uses pressurized air instead of water. Uses essential oils faster, but the scent saturation in the room is unmatched.',
   imageUrl: '/api/placeholder/400/400'
 },
 {
   id: 'prod_6',
   name: 'Frankincense Resin Tears',
   category: 'Botanicals',
   brand: 'Ancient Roots',
   price: 45.00,
   inStock: 22,
   badge: '',
   description: 'Raw, unrefined tears. Requires a charcoal burner. It’s a bit of work, but the payoff is an incredibly rich, grounded scent profile.',
   imageUrl: '/api/placeholder/400/400'
 }
];

export default function App() {
 const [searchTerm, setSearchTerm] = useState('');
 const [selectedCategory, setSelectedCategory] = useState('All Categories');

 const categories = ['All Categories', 'Devices', 'Botanicals'];

 const filteredProducts = useMemo(() => {
   return MOCK_PRODUCTS.filter(product => {
     const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       product.brand.toLowerCase().includes(searchTerm.toLowerCase());
     const matchesCategory = selectedCategory === 'All Categories' || product.category === selectedCategory;
     return matchesSearch && matchesCategory;
   });
 }, [searchTerm, selectedCategory]);

 return (
   <div className="min-h-screen bg-stone-50 text-stone-900 font-sans selection:bg-stone-300">
     {/* NAVIGATION */}
     <nav className="sticky top-0 z-50 bg-stone-50/80 backdrop-blur-md border-b border-stone-200">
       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
         <div className="flex justify-between h-16 items-center">
           <div className="flex-shrink-0 flex items-center gap-2 cursor-pointer">
             <div className="w-8 h-8 bg-stone-900 text-stone-50 rounded-sm flex items-center justify-center font-bold font-serif">
               P
             </div>
             <span className="font-semibold text-lg tracking-tight uppercase">Pixie's Pantry</span>
           </div>
           <div className="hidden md:flex space-x-8 text-sm font-medium text-stone-600">
             <a href="https://shop.pixiespantryshop.com" className="hover:text-stone-900 transition-colors">Storefront</a>
             <a href="https://pixiespantryshop.com" className="hover:text-stone-900 transition-colors">Brand</a>
             <a href="https://pixies-pantry.com" className="hover:text-stone-900 transition-colors">Business</a>
           </div>
           <div className="flex items-center gap-4">
             <button className="p-2 text-stone-500 hover:text-stone-900 transition-colors relative">
               <ShoppingCart className="w-5 h-5" />
               <span className="absolute top-1 right-1 w-2 h-2 bg-emerald-600 rounded-full"></span>
             </button>
           </div>
         </div>
       </div>
     </nav>

     {/* HERO SECTION */}
     <div className="bg-stone-900 text-stone-50 py-20 px-4 sm:px-6 lg:px-8">
       <div className="max-w-7xl mx-auto">
         <h1 className="text-4xl md:text-5xl font-light tracking-tight mb-4">
           Medusa Luxury Collection
         </h1>
         <p className="text-stone-400 text-lg max-w-2xl font-light">
           Curated premium aromatherapy devices and botanical blends.
         </p>

         {/* DUSTY'S TAKE (Persona) */}
         <div className="mt-8 p-6 bg-stone-800/50 border border-stone-700 rounded-sm max-w-3xl">
           <div className="flex items-center gap-2 mb-2 text-stone-300">
             <Info className="w-4 h-4" />
             <span className="text-sm font-bold uppercase tracking-wider">Dusty's Take</span>
           </div>
           <p className="text-sm text-stone-400 leading-relaxed">
             Look, we test a lot of gear. Most of the stuff on the market is overpriced, mass-produced plastic that breaks in a month or burns your botanicals. The devices and blends on this page are the ones that actually survive daily use. We don't do generic praise here; if it's on this list, it's because the build quality justifies the price tag and the vapor delivery is consistent. Period.
           </p>
         </div>
       </div>
     </div>

     {/* MAIN CONTENT */}
     <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
       {/* FILTER & SEARCH BAR */}
       <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 pb-6 border-b border-stone-200">
         <div className="flex flex-wrap gap-2">
           {categories.map(cat => (
             <button
               key={cat}
               onClick={() => setSelectedCategory(cat)}
               className={`px-4 py-2 text-sm font-medium rounded-sm transition-colors ${
                 selectedCategory === cat
                   ? 'bg-stone-900 text-stone-50'
                   : 'bg-stone-200 text-stone-700 hover:bg-stone-300'
               }`}
             >
               {cat}
             </button>
           ))}
           <button className="px-4 py-2 text-sm font-medium text-stone-700 bg-stone-200 rounded-sm hover:bg-stone-300 flex items-center gap-2 transition-colors">
             <Filter className="w-4 h-4" />
             More Filters
           </button>
         </div>

         <div className="relative w-full md:w-72">
           <input
             type="text"
             placeholder="Search products..."
             value={searchTerm}
             onChange={(e) => setSearchTerm(e.target.value)}
             className="w-full pl-10 pr-4 py-2 bg-stone-100 border-none rounded-sm text-sm focus:ring-2 focus:ring-stone-900 outline-none transition-shadow"
           />
           <Search className="w-4 h-4 text-stone-400 absolute left-3 top-2.5" />
         </div>
       </div>

       {/* PRODUCT GRID */}
       {filteredProducts.length === 0 ? (
         <div className="text-center py-20 text-stone-500">
           <p>No products found matching your criteria.</p>
           <button
             onClick={() => {setSearchTerm(''); setSelectedCategory('All Categories');}}
             className="mt-4 text-stone-900 underline underline-offset-4"
           >
             Clear filters
           </button>
         </div>
       ) : (
         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
           {filteredProducts.map(product => (
             <div key={product.id} className="group flex flex-col">
               {/* Image Container */}
               <div className="relative aspect-square bg-stone-200 rounded-sm mb-4 overflow-hidden">
                 <img
                   src={product.imageUrl}
                   alt={product.name}
                   className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all duration-500"
                 />
                 {/* Badges */}
                 <div className="absolute top-3 left-3 flex flex-col gap-2">
                   {product.badge && (
                     <span className={`text-xs font-bold uppercase tracking-wider px-2 py-1 rounded-sm shadow-sm ${
                       product.badge === 'Sold Out' ? 'bg-red-900 text-red-50' :
                       product.badge === 'Low Stock' ? 'bg-amber-100 text-amber-900' :
                       'bg-stone-900 text-stone-50'
                     }`}>
                       {product.badge}
                     </span>
                   )}
                 </div>
               </div>

               {/* Details */}
               <div className="flex flex-col flex-grow">
                 <div className="flex justify-between items-start mb-1">
                   <span className="text-xs font-medium text-stone-500 uppercase tracking-widest">{product.brand}</span>
                   <span className="text-sm font-semibold">${product.price.toFixed(2)}</span>
                 </div>
                 <h3 className="text-lg font-medium leading-tight mb-2 group-hover:text-emerald-700 transition-colors">
                   {product.name}
                 </h3>
                 <p className="text-sm text-stone-500 line-clamp-2 mb-4 flex-grow">
                   {product.description}
                 </p>

                 {/* Stock & Action */}
                 <div className="flex items-center justify-between mt-auto pt-4 border-t border-stone-100">
                   <span className="text-xs font-medium text-stone-500 flex items-center gap-1">
                     {product.inStock > 0 ? (
                       <>
                         <Check className="w-3 h-3 text-emerald-600" />
                         In Stock ({product.inStock})
                       </>
                     ) : (
                       <span className="text-red-600 font-semibold">Out of Stock</span>
                     )}
                   </span>
                   <button
                     disabled={product.inStock === 0}
                     className={`text-sm font-semibold uppercase tracking-wider px-4 py-2 rounded-sm transition-colors ${
                       product.inStock > 0
                         ? 'bg-stone-900 text-stone-50 hover:bg-stone-800'
                         : 'bg-stone-200 text-stone-400 cursor-not-allowed'
                     }`}
                   >
                     {product.inStock > 0 ? 'Add to Cart' : 'Notify Me'}
                   </button>
                 </div>
               </div>
             </div>
           ))}
         </div>
       )}
     </main>

     {/* FOOTER */}
     <footer className="bg-stone-900 text-stone-400 py-12 mt-20">
       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-3 gap-8">
         <div>
           <h4 className="text-stone-50 font-semibold mb-4 uppercase tracking-wider text-sm">Pixie's Pantry</h4>
           <p className="text-sm mb-4">
             Candid reviews. Premium hardware. No artificial nonsense.
           </p>
           <a href="mailto:admin@pixies-pantry.com" className="text-sm hover:text-stone-50 flex items-center gap-2 transition-colors">
             <Mail className="w-4 h-4" /> admin@pixies-pantry.com
           </a>
         </div>
         <div>
           <h4 className="text-stone-50 font-semibold mb-4 uppercase tracking-wider text-sm">Community</h4>
           <div className="flex flex-col gap-3">
             <a href="https://discord.com/invite/SvQQtHHk" target="_blank" rel="noreferrer" className="text-sm hover:text-stone-50 flex items-center gap-2 transition-colors">
               <MessageSquare className="w-4 h-4" /> Discord Server
             </a>
             <a href="https://www.youtube.com/channel/UCpQhd79nWMsFnwZgI_Okeuw" target="_blank" rel="noreferrer" className="text-sm hover:text-stone-50 flex items-center gap-2 transition-colors">
               <Youtube className="w-4 h-4" /> YouTube Channel
             </a>
             <a href="https://www.instagram.com/pixiespantryshop/" target="_blank" rel="noreferrer" className="text-sm hover:text-stone-50 flex items-center gap-2 transition-colors">
               <Instagram className="w-4 h-4" /> Instagram
             </a>
           </div>
         </div>
         <div>
           <h4 className="text-stone-50 font-semibold mb-4 uppercase tracking-wider text-sm">Domains</h4>
           <div className="flex flex-col gap-3">
             <a href="https://shop.pixiespantryshop.com" className="text-sm hover:text-stone-50 transition-colors">Main Storefront</a>
             <a href="https://pixiespantryshop.com" className="text-sm hover:text-stone-50 transition-colors">Brand Domain</a>
             <a href="https://pixies-pantry.com" className="text-sm hover:text-stone-50 transition-colors">Business Hub</a>
           </div>
         </div>
       </div>
       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12 pt-8 border-t border-stone-800 text-xs text-center">
         &copy; {new Date().getFullYear()} Pixie's Pantry. All rights reserved.
       </div>
     </footer>
   </div>
 );
}