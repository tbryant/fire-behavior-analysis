# 🌐 GitHub Pages Setup

Your fire analysis visualizations are now hosted on GitHub Pages!

## 📍 Your Live Site

**URL:** https://tbryant.github.io/fire-behavior-analysis/

The site is currently building. It will be live in 1-2 minutes.

## 🔄 Updating Your Visualizations

Whenever you create a new fire analysis map, use the `update_pages.py` script:

### Basic Update (Replace Main Page)
```bash
# Update with latest healdsburg map (default)
python update_pages.py

# Or specify a different file
python update_pages.py --source outputs/my_analysis.html
```

### Add Multiple Maps
```bash
# Add additional pages without replacing index
python update_pages.py --source outputs/region1.html --name region1 --no-index
python update_pages.py --source outputs/region2.html --name region2 --no-index

# Create an index page listing all maps
python update_pages.py --create-index
```

### Publish Your Changes
```bash
git add docs/
git commit -m "Update fire visualization"
git push
```

Your changes will be live within 1-2 minutes!

## 📋 Available Commands

```bash
# List all published pages
python update_pages.py --list

# Update main page
python update_pages.py

# Add a named page
python update_pages.py --source outputs/map.html --name custom_region

# Create index of all pages
python update_pages.py --create-index

# Help
python update_pages.py --help
```

## 🎨 Customization

### Modify the Main Page
Edit `docs/README.md` to customize the description shown on GitHub.

### Add Custom Styling
Create a `docs/style.css` file and link it in your HTML files.

### Custom Domain (Optional)
1. Go to repository Settings → Pages
2. Add your custom domain
3. Configure DNS records as instructed

## 📤 Sharing Your Maps

Share your live map with anyone using the URL:
```
https://tbryant.github.io/fire-behavior-analysis/
```

They can view the interactive map without:
- Installing Python
- Downloading LANDFIRE data
- Running any scripts

Perfect for:
- Client presentations
- Stakeholder reviews
- Public outreach
- Portfolio demonstrations

## 🔧 Troubleshooting

### Page Not Updating?
1. Check GitHub Actions status: `gh run list --limit 5`
2. Wait 1-2 minutes for build to complete
3. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

### Build Failed?
```bash
# Check Pages build status
gh api repos/tbryant/fire-behavior-analysis/pages

# View recent workflow runs
gh run list --limit 5
```

### Need to Start Over?
```bash
# Disable Pages
gh api repos/tbryant/fire-behavior-analysis/pages -X DELETE

# Re-enable
gh api repos/tbryant/fire-behavior-analysis/pages -X POST \
  -f source[branch]=main -f source[path]=/docs
```

## 📚 Learn More

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Custom Domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
- [Jekyll Themes](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll) (optional)
