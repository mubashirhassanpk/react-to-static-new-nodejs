import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Download, ExternalLink, CheckCircle2, XCircle, Clock, Loader2, Cloud } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function BuildDetails() {
  const { buildId } = useParams();
  const navigate = useNavigate();
  const [build, setBuild] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Netlify deployment states
  const [netlifyToken, setNetlifyToken] = useState("");
  const [netlifySiteId, setNetlifySiteId] = useState("");
  const [isDeploying, setIsDeploying] = useState(false);

  useEffect(() => {
    fetchBuildStatus();
    const interval = setInterval(() => {
      fetchBuildStatus();
    }, 3000);

    return () => clearInterval(interval);
  }, [buildId]);

  const fetchBuildStatus = async () => {
    try {
      const response = await axios.get(`${API}/build/status/${buildId}`);
      setBuild(response.data);
      setLoading(false);
    } catch (error) {
      toast.error("Failed to fetch build status");
      setLoading(false);
    }
  };

  const handleDownload = () => {
    window.open(`${API}/build/download/${buildId}`, "_blank");
    toast.success("Download started!");
  };

  const handlePreview = () => {
    window.open(`${API}/build/preview/${buildId}/index.html`, "_blank");
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "pending":
        return <Clock className="w-5 h-5 text-yellow-600" />;
      case "building":
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case "completed":
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case "pending":
        return "status-pending";
      case "building":
        return "status-building";
      case "completed":
        return "status-completed";
      case "failed":
        return "status-failed";
      default:
        return "";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading build details...</p>
        </div>
      </div>
    );
  }

  if (!build) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Build not found</p>
          <Button onClick={() => navigate("/")} className="mt-4">
            Go Home
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 md:p-12">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate("/")}
            className="btn-secondary inline-flex items-center gap-2 mb-4"
            data-testid="back-button"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </button>
          <h1 className="text-4xl font-bold gradient-text mb-2">Build Details</h1>
          <p className="text-gray-600">Build ID: {buildId}</p>
        </div>

        {/* Status Card */}
        <Card className="glass-card p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-semibold">Status</h2>
              <span className={`status-badge ${getStatusClass(build.status)}`}>
                {getStatusIcon(build.status)}
                {build.status.toUpperCase()}
              </span>
            </div>
            {build.status === "completed" && (
              <div className="flex gap-3">
                <button
                  onClick={handlePreview}
                  className="btn-secondary inline-flex items-center gap-2"
                  data-testid="preview-button"
                >
                  <ExternalLink className="w-4 h-4" />
                  Preview
                </button>
                <button
                  onClick={handleDownload}
                  className="btn-primary inline-flex items-center gap-2"
                  data-testid="download-button"
                >
                  <Download className="w-4 h-4" />
                  Download ZIP
                </button>
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Input Type</p>
              <p className="font-semibold capitalize">{build.input_type}</p>
            </div>
            <div>
              <p className="text-gray-500">Created At</p>
              <p className="font-semibold">
                {new Date(build.created_at).toLocaleString()}
              </p>
            </div>
          </div>
          {build.error_message && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 font-semibold mb-1">Error:</p>
              <p className="text-red-700 text-sm">{build.error_message}</p>
            </div>
          )}
        </Card>

        {/* Build Logs */}
        <Card className="glass-card p-6">
          <h2 className="text-2xl font-semibold mb-4">Build Logs</h2>
          <div className="build-log" data-testid="build-logs">
            {build.build_logs || "No logs available yet..."}
          </div>
        </Card>
      </div>
    </div>
  );
}