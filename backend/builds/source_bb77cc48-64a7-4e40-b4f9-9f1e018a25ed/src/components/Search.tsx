
import React, { useState } from 'react';
import { Search as SearchIcon } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { useToast } from './ui/use-toast';

const Search = ({ onSearch }: { onSearch: (query: string) => void }) => {
  const [query, setQuery] = useState('');
  const { toast } = useToast();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      toast({
        title: "সার্চ টার্ম প্রয়োজন",
        description: "অনুগ্রহ করে কিছু লিখুন",
        variant: "destructive",
      });
      return;
    }
    onSearch(query);
  };

  return (
    <form onSubmit={handleSearch} className="w-full max-w-2xl mx-auto">
      <div className="relative flex items-center gap-2">
        <Input
          type="text"
          placeholder="ছবি খুঁজুন..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full backdrop-blur-sm bg-white/80 border-2 focus-visible:ring-0 focus-visible:ring-offset-0 transition-all duration-300"
        />
        <Button 
          type="submit"
          className="absolute right-2 hover:scale-105 transition-transform duration-300"
          variant="ghost"
          size="icon"
        >
          <SearchIcon className="w-5 h-5" />
        </Button>
      </div>
    </form>
  );
};

export default Search;
