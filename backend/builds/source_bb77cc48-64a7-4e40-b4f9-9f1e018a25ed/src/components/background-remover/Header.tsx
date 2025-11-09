
import { Crown, Sparkles } from 'lucide-react';

export const Header = () => {
  return (
    <div className="text-center space-y-6 animate-fade-in">
      <div className="relative inline-block">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 text-transparent bg-clip-text">
          ULTRA HD BACKGROUND REMOVER
        </h1>
        <div className="absolute -top-4 -right-4 animate-bounce">
          <Crown className="w-8 h-8 text-yellow-500" />
        </div>
      </div>
      <div className="flex items-center justify-center gap-2">
        <Sparkles className="w-5 h-5 text-purple-500 animate-pulse" />
        <p className="text-gray-600 text-lg">
          Remove backgrounds instantly - <span className="font-bold text-green-500">100% FREE!</span>
        </p>
        <Sparkles className="w-5 h-5 text-purple-500 animate-pulse" />
      </div>
    </div>
  );
};
