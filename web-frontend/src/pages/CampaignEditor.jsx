import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCampaign, updateCampaign, uploadCampaignVideo, deleteCampaignVideo, getCampaignVideo } from '../api/campaigns';
import useAuthStore from '../stores/authStore';
import VideoPlayer from '../components/VideoPlayer';
import {
  HiOutlineArrowLeft, HiOutlineMapPin, HiOutlineFilm,
  HiOutlineVideoCameraSlash, HiOutlineCheckCircle,
} from '../components/icons';
import { PageBg, PageHeader } from '../components/SvgDecorations';

const CATEGORIES = ['water', 'education', 'health', 'infrastructure', 'food', 'environment', 'shelter', 'children'];

export default function CampaignEditor() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [campaign, setCampaign] = useState(null);
  const [video, setVideo] = useState(null);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [videoUploading, setVideoUploading] = useState(false);
  const [videoDeleting, setVideoDeleting] = useState(false);

  useEffect(() => {
    if (!user) { navigate('/login'); return; }
    (async () => {
      setLoading(true);
      try {
        const c = await getCampaign(id);
        setCampaign(c);
        setForm({
          title: c.title || '',
          description: c.description || '',
          category: c.category || '',
          goal_amount_usd: c.goal_amount_usd || '',
          status: c.status || 'active',
          location_gps: c.location_gps || '',
        });
        try { const vd = await getCampaignVideo(id); setVideo(vd.video || vd); } catch { /* no video */ }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id, user]);

  const set = (field, value) => { setForm((prev) => ({ ...prev, [field]: value })); setSaved(false); };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const payload = {};
      if (form.title !== campaign.title) payload.title = form.title;
      if (form.description !== campaign.description) payload.description = form.description;
      if (form.category !== (campaign.category || '')) payload.category = form.category || undefined;
      if (parseFloat(form.goal_amount_usd) !== campaign.goal_amount_usd) payload.goal_amount_usd = parseFloat(form.goal_amount_usd);
      if (form.status !== campaign.status) payload.status = form.status;
      if (form.location_gps !== (campaign.location_gps || '')) payload.location_gps = form.location_gps || undefined;
      if (Object.keys(payload).length > 0) {
        const updated = await updateCampaign(id, payload);
        setCampaign(updated);
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleVideoUpload = async () => {
    if (!videoFile) return;
    setVideoUploading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('video', videoFile);
      await uploadCampaignVideo(id, fd);
      setVideoFile(null);
      try { const vd = await getCampaignVideo(id); setVideo(vd.video || vd); } catch { /* */ }
    } catch (err) {
      setError(err.message);
    } finally {
      setVideoUploading(false);
    }
  };

  const handleVideoDelete = async () => {
    if (!confirm('Delete the transparency video? This cannot be undone.')) return;
    setVideoDeleting(true);
    try {
      await deleteCampaignVideo(id);
      setVideo(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setVideoDeleting(false);
    }
  };

  const getLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => set('location_gps', `${pos.coords.latitude},${pos.coords.longitude}`),
      () => {}, { enableHighAccuracy: true }
    );
  };

  if (loading) return <div className="text-center py-20 text-gray-400">Loading…</div>;
  if (error && !campaign) return <div className="text-center py-20 text-red-400">{error}</div>;

  return (
    <PageBg pattern="topography" colorA="#7C3AED" colorB="#6366F1">
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <Link to="/my-projects" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline">
          <HiOutlineArrowLeft className="w-4 h-4" /> My Projects
        </Link>
        <Link to={`/campaign/${id}`} className="text-xs text-gray-400 hover:text-gray-600 transition">View public page →</Link>
      </div>

      <PageHeader icon={HiOutlineMapPin} title="Edit Campaign" subtitle={campaign?.title} accentColor="violet" bespoke="topography" />

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}
      {saved && <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 mb-4 text-sm text-emerald-600 flex items-center gap-2"><HiOutlineCheckCircle className="w-4 h-4" /> Changes saved</div>}

      {/* Core fields */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-6 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-violet-500 to-transparent" />
        <svg className="absolute top-2 right-2 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
          <circle cx="60" cy="20" r="15" stroke="#7C3AED" strokeWidth="0.5" opacity="0.04" />
          <path d="M55 18 L60 12 L65 18" stroke="#7C3AED" strokeWidth="0.4" opacity="0.03" />
        </svg>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input type="text" value={form.title} onChange={(e) => set('title', e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea rows={5} value={form.description} onChange={(e) => set('description', e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select value={form.category} onChange={(e) => set('category', e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition text-sm capitalize">
                <option value="">None</option>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select value={form.status} onChange={(e) => set('status', e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition text-sm">
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Funding Goal (USD)</label>
              <input type="number" min={1} value={form.goal_amount_usd} onChange={(e) => set('goal_amount_usd', e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">GPS Location</label>
              <div className="flex gap-2">
                <input type="text" placeholder="-1.286,36.817" value={form.location_gps} onChange={(e) => set('location_gps', e.target.value)}
                  className="flex-1 px-3 py-2.5 rounded-xl border border-gray-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition text-sm" />
                <button onClick={getLocation} className="px-3 py-2.5 rounded-xl bg-gray-100 hover:bg-gray-200 transition" title="Use current location">
                  <HiOutlineMapPin className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>
          </div>

          <button onClick={handleSave} disabled={saving}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold hover:from-indigo-700 hover:to-violet-700 transition disabled:opacity-50 text-sm">
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Video section */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-6 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-rose-500 via-pink-500 to-transparent" />
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <HiOutlineFilm className="w-4 h-4 text-rose-500" /> Transparency Video
        </h3>

        {video ? (
          <div className="space-y-3">
            <VideoPlayer videoData={video} />
            <button onClick={handleVideoDelete} disabled={videoDeleting}
              className="text-xs text-red-500 hover:text-red-700 font-medium transition">
              {videoDeleting ? 'Deleting…' : 'Delete video'}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-6 text-center text-gray-400 text-sm flex flex-col items-center gap-2">
              <HiOutlineVideoCameraSlash className="w-8 h-8 text-gray-300" />
              No transparency video uploaded
            </div>
            <div className="flex items-center gap-3">
              <input type="file" accept="video/mp4,video/mov,video/avi,video/webm"
                onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                className="flex-1 text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:text-indigo-700 file:text-xs file:font-semibold hover:file:bg-indigo-100" />
              <button onClick={handleVideoUpload} disabled={!videoFile || videoUploading}
                className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition disabled:opacity-50">
                {videoUploading ? 'Uploading…' : 'Upload'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Quick links */}
      <div className="flex flex-wrap gap-2">
        <Link to={`/campaign/${id}/milestones`} className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-violet-50 text-violet-700 text-xs font-semibold hover:bg-violet-100 transition border border-violet-100">
          <HiOutlineCheckCircle className="w-3.5 h-3.5" /> Manage Milestones
        </Link>
        <Link to={`/campaign/${id}/financials`} className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 transition border border-emerald-100">
          Financials
        </Link>
        <Link to={`/campaign/${id}/updates`} className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-blue-50 text-blue-700 text-xs font-semibold hover:bg-blue-100 transition border border-blue-100">
          Project Updates
        </Link>
      </div>
    </div>
    </PageBg>
  );
}
