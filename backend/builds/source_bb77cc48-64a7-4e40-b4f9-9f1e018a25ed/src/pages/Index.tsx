
import BackgroundRemover from '@/components/BackgroundRemover';

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-100 via-pink-50 to-teal-50 animate-gradient-xy">
      <BackgroundRemover />
      <footer className="mt-auto py-4 text-center text-gray-600">
        <a 
          href="https://www.dreamit.digital" 
          target="_blank" 
          rel="noopener noreferrer"
          className="hover:text-purple-600 transition-colors duration-300"
        >
          made by dreamit.digital
        </a>
      </footer>
    </div>
  );
};

export default Index;
