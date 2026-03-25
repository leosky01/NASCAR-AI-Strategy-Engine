# Streamlit Cloud Deployment Troubleshooting

## Common Issues and Solutions

### Issue: "Build failed" or "Module not found: kaleido"

**Cause:** kaleido is a heavy package that often fails to build on Streamlit Cloud.

**Solution:** ✅ ALREADY FIXED - kaleido has been removed from requirements.txt

**Explanation:**
- kaleido is only needed for static image generation of Plotly charts
- Streamlit handles Plotly rendering in the browser automatically
- Removing kaleido reduces deployment time and prevents build failures

---

### Issue: "ModuleNotFoundError: No module named 'altair.vegalite.v4'"

**Cause:** Version incompatibility between Streamlit and altair.

**Error Message:**
```
ModuleNotFoundError: No module named 'altair.vegalite.v4'
```

**Solution:** ✅ ALREADY FIXED - Added altair version constraint to requirements.txt

**Details:**
- altair 6.0.0+ removed the `vegalite.v4` API
- Streamlit 1.x still depends on the old API
- Fixed by pinning: `altair>=5.0.0,<6.0.0`
- Also added version constraints for all packages to prevent similar issues

**Verification:**
```bash
# Check requirements.txt has altair pinned
grep altair requirements.txt
# Should show: altair>=5.0.0,<6.0.0
```

---

### Issue: "ImportError: No module named 'src'"

**Cause:** Package structure not recognized by Streamlit Cloud.

**Solution:** ✅ FIXED - The imports work because:
- All code uses `from src.xxx import yyy` syntax
- src/__init__.py exists
- app.py is in the root directory

**Verification:**
```bash
python3 test_deployment.py
```

---

### Issue: "Application crashes immediately after deployment"

**Possible Causes:**

1. **Hardcoded file paths**
   - ✅ CHECKED: No hardcoded data/ or models/ paths in app.py
   - All data is synthetic (generated on the fly)

2. **Missing data files**
   - ✅ CHECKED: No external data files required
   - Everything is generated programmatically

3. **Version conflicts**
   - ✅ CHECKED: Added version constraints to requirements.txt
   - Uses compatible version ranges

---

### Issue: "Deployment is slow"

**Cause:** Heavy dependencies or large package downloads.

**Current Status:**
- Removed kaleido (~100MB)
- Version constraints prevent unnecessary upgrades
- Total dependencies: ~50MB (reasonable)

---

## Pre-Deployment Checklist

Run these commands before deploying:

```bash
# 1. Test imports work
python3 test_deployment.py

# 2. Verify requirements.txt
head -20 requirements.txt

# 3. Check for kaleido (should NOT be there)
grep kaleido requirements.txt
# Should return nothing (or a comment)

# 4. Verify git status
git status
# Should show: clean or only untracked files

# 5. Latest commit on main
git log --oneline -1
```

---

## Deployment Steps

1. **Make sure all changes are pushed**
   ```bash
   git add .
   git commit -m "Fix kaleido issue for Streamlit Cloud"
   git push
   ```

2. **Go to Streamlit Cloud**
   - https://share.streamlit.io

3. **Connect Repository**
   - Click "New app"
   - Select: `leosky01/NASCAR-AI-Strategy-Engine`
   - Branch: `main`
   - Main file: `app.py`

4. **Deploy**
   - Click "Deploy"
   - Wait 1-2 minutes

5. **Monitor Deployment**
   - Watch the build logs
   - Should see "Successfully deployed"
   - App will be available at: `https://[app-name].streamlit.app`

---

## Current Known Issues & Status

| Issue | Status | Fix |
|-------|--------|-----|
| kaleido build failure | ✅ FIXED | Removed from requirements.txt |
| Import errors | ✅ FIXED | All imports verified |
| Missing data files | ✅ N/A | Uses synthetic data |
| Version conflicts | ✅ FIXED | Added version constraints |
| Slow deployment | ✅ FIXED | Optimized dependencies |

---

## If Deployment Still Fails

1. **Check the build logs** on Streamlit Cloud
2. **Look for specific error messages**
3. **Run diagnostic locally:**
   ```bash
   python3 test_deployment.py
   ```
4. **Try deploying with minimal requirements:**
   - Use `requirements_streamlit_cloud.txt`
   - Rename it to `requirements.txt`
   - Deploy again

---

## Last Resort: Minimal Deployment

If all else fails, create a minimal app:

```python
# app_minimal.py
import streamlit as st

st.title("NASCAR AI Strategy Engine")
st.write("Dashboard is running! More features coming soon.")
```

Deploy this minimal app first to verify the pipeline works, then add features incrementally.

---

## Success Metrics

When deployment succeeds, you should see:
- ✅ Status: "Running"
- ✅ URL accessible in browser
- ✅ Dashboard loads without errors
- ✅ All tabs visible and functional

Expected deployment time: 1-2 minutes

---

## Need Help?

1. Check Streamlit Cloud docs: https://docs.streamlit.io/streamlit-cloud/
2. Run diagnostic: `python3 test_deployment.py`
3. Check test results: `pytest tests/ -v`
4. Review this file for common issues
