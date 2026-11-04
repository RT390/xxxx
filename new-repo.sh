#!/data/data/com.termux/files/usr/bin/bash
# =====================================================
#  إنشاء مستودع جديد ورفع الملفات له
# =====================================================

set -e
clear

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; NC='\033[0m'

PROJECT="/storage/emulated/0/data"

echo -e "${CYAN}━━━ إنشاء مستودع جديد ━━━${NC}"
cd "$PROJECT" || { echo -e "${RED}❌ $PROJECT مو موجود${NC}"; exit 1; }

# ============ جمع المعلومات ============
read -p "👤 GitHub Username (RT390): " GH_USER
GH_USER=${GH_USER:-RT390}

read -p "📦 اسم المستودع الجديد (fatwa-bot): " REPO
REPO=${REPO:-fatwa-bot}

read -sp "🔑 GitHub Token: " GH_TOKEN
echo ""
[ -z "$GH_TOKEN" ] && echo -e "${RED}❌ التوكن مطلوب${NC}" && exit 1

read -p "📧 Email (اختياري): " GH_EMAIL
GH_EMAIL=${GH_EMAIL:-"$GH_USER@users.noreply.github.com"}

# ============ تأكيد ============
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  المستخدم:  ${GREEN}$GH_USER${NC}"
echo -e "  المستودع:  ${GREEN}$REPO${NC}"
echo -e "  الإيميل:   ${GREEN}$GH_EMAIL${NC}"
echo -e "  المشروع:   ${GREEN}$PROJECT${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
read -p "متابعة؟ (y/n): " C
[ "$C" != "y" ] && echo "ألغي" && exit 0

# ============ 1. إنشاء المستودع على GitHub ============
echo ""
echo -e "${CYAN}[1/6]${NC} إنشاء المستودع على GitHub..."

CREATE_RESP=$(curl -s -X POST \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"$REPO\",\"private\":false,\"auto_init\":false}")

# تحقق من النتيجة
if echo "$CREATE_RESP" | grep -q '"full_name"'; then
    echo -e "${GREEN}✅ تم إنشاء المستودع${NC}"
elif echo "$CREATE_RESP" | grep -q '"message": "name already exists"'; then
    echo -e "${YELLOW}⚠️  المستودع موجود مسبقاً، بنستخدمه${NC}"
else
    echo -e "${RED}❌ فشل إنشاء المستودع:${NC}"
    echo "$CREATE_RESP" | head -20
    exit 1
fi

# ============ 2. حذف git القديم ============
echo -e "${CYAN}[2/6]${NC} تنظيف git القديم..."
rm -rf .git

# ============ 3. git init جديد ============
echo -e "${CYAN}[3/6]${NC} git init..."
git init -q
git config user.name "$GH_USER"
git config user.email "$GH_EMAIL"
git branch -M main
git config --global --add safe.directory "$PROJECT" 2>/dev/null || true

# ============ 4. إضافة الملفات ============
echo -e "${CYAN}[4/6]${NC} إضافة الملفات..."

# تأكد من .gitignore
if [ ! -f .gitignore ]; then
    printf '.env\n__pycache__/\n*.pyc\nlogs/\ntmp/\n*.mp4\n*.mp3\nconfig.py.bak\n.DS_Store\nvenv/\n' > .gitignore
fi

git add -A
git commit -q -m "initial: fatwa bot full upload"
echo -e "${GREEN}✅ commit جاهز${NC}"

# ============ 5. ربط ورفع ============
echo -e "${CYAN}[5/6]${NC} رفع إلى GitHub..."
git remote add origin "https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/${REPO}.git"

if git push -u origin main --force 2>&1 | tee /tmp/push.log; then
    echo -e "${GREEN}✅ تم الرفع${NC}"
else
    echo -e "${RED}❌ فشل الرفع${NC}"
    cat /tmp/push.log
    exit 1
fi

# ============ 6. تنظيف التوكن ============
git remote set-url origin "https://github.com/${GH_USER}/${REPO}.git"

# ============ نتيجة ============
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✅ اكتمل بنجاح!              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo -e "🔗 ${CYAN}https://github.com/${GH_USER}/${REPO}${NC}"
echo ""
echo -e "${YELLOW}📌 خطوات Render:${NC}"
echo ""
echo "   1. https://dashboard.render.com"
echo "   2. احذف Blueprint القديم (BOOT و BOOT2)"
echo "   3. احذف Database القديمة (fatwa-db)"
echo "   4. New + → Blueprint"
echo "   5. اختر: ${GREEN}${GH_USER}/${REPO}${NC}"
echo "   6. املأ BOT_TOKEN + DASHBOARD_PASSWORD"
echo "   7. Deploy"
echo ""
echo -e "${YELLOW}⚠️  لكن أول — عدّل render.yaml:${NC}"
echo "   غير اسم الريبو لو غيرت الاسم"
echo ""
