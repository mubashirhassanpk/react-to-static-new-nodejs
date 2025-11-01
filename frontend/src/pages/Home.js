import { useState } from "react";
import { Upload, Code, Github, FileCode, Zap, Download } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { getApiUrl } from "@/utils/backend";

const API = getApiUrl();

export default function Home() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [code, setCode] = useState(
    `import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Hello from React!</h1>
      <p>This is a sample React component.</p>
    </div>
  );
}

export default App;`
  );
  const [githubUrl, setGithubUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith(".zip")) {
        setSelectedFile(file);
        toast.success(`File selected: ${file.name}`);
      } else {
        toast.error("Please upload a ZIP file");
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith(".zip")) {
        setSelectedFile(file);
        toast.success(`File selected: ${file.name}`);
      } else {
        toast.error("Please upload a ZIP file");
      }
    }
  };

  const handleUploadBuild = async () => {
    if (!selectedFile) {
      toast.error("Please select a file first");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(`${API}/build/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Build started! Redirecting...");
      setTimeout(() => navigate(`/build/${response.data.id}`), 1000);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to start build");
      setLoading(false);
    }
  };

  const handlePasteBuild = async () => {
    if (!code.trim()) {
      toast.error("Please enter some code");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/build/paste`, {
        code,
        filename: "App.js",
      });
      toast.success("Build started! Redirecting...");
      setTimeout(() => navigate(`/build/${response.data.id}`), 1000);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to start build");
      setLoading(false);
    }
  };

  const handleGithubBuild = async () => {
    if (!githubUrl.trim()) {
      toast.error("Please enter a GitHub URL");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/build/github`, {
        repo_url: githubUrl,
      });
      toast.success("Build started! Redirecting...");
      setTimeout(() => navigate(`/build/${response.data.id}`), 1000);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to start build");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-6 md:p-12">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12 fade-in">
          <div className="flex items-center justify-center gap-3 mb-4">
            <FileCode className="w-12 h-12 text-blue-500" />
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold gradient-text">
              Reactly
            </h1>
          </div>
          <p className="text-base md:text-lg text-gray-600 max-w-2xl mx-auto mb-2">
            Convert your React projects to production-ready static sites automatically.
            Upload, paste, or connect your GitHub repo.
          </p>
          <p className="text-sm text-gray-500">
            <a href="https://www.reactly.site" target="_blank" rel="noopener noreferrer" className="hover:text-blue-500 transition-colors">
              www.reactly.site
            </a>
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 fade-in">
          <Card className="glass-card p-6">
            <Zap className="w-10 h-10 text-blue-500 mb-3" />
            <h3 className="text-xl font-semibold mb-2">Automatic Build</h3>
            <p className="text-gray-600 text-sm">
              We run npm install & npm run build automatically in the background
            </p>
          </Card>
          <Card className="glass-card p-6">
            <Download className="w-10 h-10 text-blue-500 mb-3" />
            <h3 className="text-xl font-semibold mb-2">Download & Preview</h3>
            <p className="text-gray-600 text-sm">
              Get your static build as a ZIP file and preview it instantly
            </p>
          </Card>
          <Card className="glass-card p-6">
            <Code className="w-10 h-10 text-blue-500 mb-3" />
            <h3 className="text-xl font-semibold mb-2">Multiple Inputs</h3>
            <p className="text-gray-600 text-sm">
              Support for ZIP uploads, code paste, and GitHub repositories
            </p>
          </Card>
        </div>

        {/* Main Build Interface */}
        <Card className="glass-card p-8 fade-in">
          <Tabs defaultValue="upload" className="w-full">
            <TabsList className="grid w-full grid-cols-3 mb-8">
              <TabsTrigger value="upload" data-testid="upload-tab">
                <Upload className="w-4 h-4 mr-2" />
                Upload ZIP
              </TabsTrigger>
              <TabsTrigger value="paste" data-testid="paste-tab">
                <Code className="w-4 h-4 mr-2" />
                Paste Code
              </TabsTrigger>
              <TabsTrigger value="github" data-testid="github-tab">
                <Github className="w-4 h-4 mr-2" />
                GitHub Repo
              </TabsTrigger>
            </TabsList>

            {/* Upload Tab */}
            <TabsContent value="upload" className="space-y-4">
              <div
                className={`upload-zone ${dragActive ? "drag-active" : ""}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById("file-upload").click()}
                data-testid="upload-zone"
              >
                <Upload className="w-16 h-16 mx-auto mb-4 text-blue-500" />
                <p className="text-lg font-semibold text-gray-700 mb-2">
                  {selectedFile ? selectedFile.name : "Drop your React project ZIP here"}
                </p>
                <p className="text-sm text-gray-500">or click to browse</p>
                <input
                  id="file-upload"
                  type="file"
                  accept=".zip"
                  onChange={handleFileChange}
                  className="hidden"
                  data-testid="file-input"
                />
              </div>
              <div className="text-center">
                <button
                  className="btn-primary"
                  onClick={handleUploadBuild}
                  disabled={loading || !selectedFile}
                  data-testid="upload-build-btn"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="spinner"></div>
                      Building...
                    </span>
                  ) : (
                    "Start Build"
                  )}
                </button>
              </div>
            </TabsContent>

            {/* Paste Tab */}
            <TabsContent value="paste" className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Paste your React component code:
                </label>
                <Textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="code-editor min-h-[300px] font-mono text-sm"
                  placeholder="Paste your React code here..."
                  data-testid="code-textarea"
                />
              </div>
              <div className="text-center">
                <button
                  className="btn-primary"
                  onClick={handlePasteBuild}
                  disabled={loading}
                  data-testid="paste-build-btn"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="spinner"></div>
                      Building...
                    </span>
                  ) : (
                    "Start Build"
                  )}
                </button>
              </div>
            </TabsContent>

            {/* GitHub Tab */}
            <TabsContent value="github" className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  GitHub Repository URL:
                </label>
                <Input
                  type="text"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/username/repo"
                  className="text-base"
                  data-testid="github-input"
                />
                <p className="text-sm text-gray-500 mt-2">
                  Make sure the repository is public and contains a valid React project
                </p>
              </div>
              <div className="text-center">
                <button
                  className="btn-primary"
                  onClick={handleGithubBuild}
                  disabled={loading}
                  data-testid="github-build-btn"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="spinner"></div>
                      Building...
                    </span>
                  ) : (
                    "Start Build"
                  )}
                </button>
              </div>
            </TabsContent>
          </Tabs>
        </Card>

        {/* Footer */}
        <div className="text-center mt-12 text-sm text-gray-500">
          <p className="mb-2">
            Developed by{" "}
            <a 
              href="https://www.mubashirhassan.com" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-blue-500 hover:text-blue-600 transition-colors font-medium"
            >
              Mubashir Hassan
            </a>
          </p>
          <p className="flex items-center justify-center gap-4 flex-wrap">
            <a 
              href="mailto:hello@mubashirhassan.com" 
              className="hover:text-blue-500 transition-colors"
            >
              hello@mubashirhassan.com
            </a>
            <span className="text-gray-400">•</span>
            <a 
              href="https://wa.me/923222047786" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="hover:text-blue-500 transition-colors"
            >
              WhatsApp: +92 322 2047786
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}