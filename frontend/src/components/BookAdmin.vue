<template>
  <div class="book-admin">
    <div class="admin-head">
      <div>
        <div class="panel-t">书籍管理</div>
        <p class="hint">管理员创建的书会直接出现在 CyberRange 图书馆书架上。</p>
      </div>
      <div class="create-row">
        <input v-model="createTitle" placeholder="输入新书名称" @keyup.enter="createBook" />
        <button class="btn primary" :disabled="!createTitle.trim() || creating" @click="createBook">
          {{ creating ? '创建中…' : '+ 新建书籍' }}
        </button>
      </div>
    </div>

    <div class="book-layout">
      <aside class="book-list">
        <button
          v-for="book in books"
          :key="book.id"
          class="book-item"
          :class="{ active: selected?.id === book.id }"
          type="button"
          @click="selectBook(book.id)"
        >
          <span class="book-title">{{ book.title }}</span>
          <span class="book-meta">{{ book.page_count }} 页</span>
        </button>
        <div v-if="!loading && books.length === 0" class="empty">还没有书籍</div>
      </aside>

      <section v-if="selected" class="book-editor">
        <div class="book-title-row">
          <input v-model="editorTitle" class="title-input" />
          <button class="btn" :disabled="savingBook || !editorTitle.trim()" @click="saveBookTitle">保存名称</button>
          <button class="btn danger" @click="deleteBook">删除书籍</button>
        </div>

        <div class="page-layout">
          <nav class="page-list">
            <button
              v-for="page in selected.pages"
              :key="page.id"
              class="page-item"
              :class="{ active: currentPage?.id === page.id }"
              type="button"
              @click="selectPage(page.id)"
            >
              第 {{ page.position }} 页
            </button>
          </nav>

          <div v-if="currentPage" class="page-editor">
            <div class="page-head">
              <span>第 {{ currentPage.position }} 页</span>
              <span>{{ selected.title }}</span>
            </div>

            <label class="field">
              <span>页面文字</span>
              <textarea
                v-model="pageContent"
                rows="14"
                placeholder="输入这一页的文字内容…"
              />
            </label>

            <div class="image-row">
              <label class="upload-btn">
                <input type="file" accept="image/*" @change="uploadImage" />
                {{ uploading ? '上传中…' : '上传图片' }}
              </label>
              <button v-if="pageImage" class="btn danger" @click="pageImage = null">移除图片</button>
            </div>

            <div v-if="pageImage" class="image-preview">
              <img :src="bookImageUrl(pageImage)" alt="页面图片预览" />
            </div>

            <div class="page-actions">
              <button class="btn primary" :disabled="savingPage" @click="savePage">
                {{ savingPage ? '保存中…' : '保存当前页' }}
              </button>
              <button class="btn" @click="insertPageAfter">+ 在当前页后插入</button>
              <button
                class="btn danger"
                :disabled="selected.pages.length <= 1"
                @click="deletePage"
              >删除当前页</button>
            </div>
          </div>
        </div>
      </section>

      <section v-else class="book-empty">
        <span>选择左侧书籍开始编辑</span>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  booksApi,
  bookImageUrl,
  type BookDetail,
  type BookPage,
  type BookSummary,
} from '../api/books'

const books = ref<BookSummary[]>([])
const selected = ref<BookDetail | null>(null)
const currentPage = computed(
  () => selected.value?.pages.find((page) => page.id === activePageId.value) ?? null,
)
const activePageId = ref<number | null>(null)

const loading = ref(true)
const creating = ref(false)
const savingBook = ref(false)
const savingPage = ref(false)
const uploading = ref(false)
const createTitle = ref('')
const editorTitle = ref('')
const pageContent = ref('')
const pageImage = ref<string | null>(null)

function applyPage(page: BookPage) {
  activePageId.value = page.id
  pageContent.value = page.content
  pageImage.value = page.image
}

function applyBook(book: BookDetail) {
  selected.value = book
  editorTitle.value = book.title
  const keepCurrent = book.pages.find((page) => page.id === activePageId.value)
  applyPage(keepCurrent ?? book.pages[0])
}

async function loadBooks() {
  loading.value = true
  try {
    books.value = await booksApi.adminList()
  } finally {
    loading.value = false
  }
}

async function selectBook(id: number) {
  activePageId.value = null
  const book = await booksApi.get(id)
  applyBook(book)
}

async function createBook() {
  const title = createTitle.value.trim()
  if (!title) return
  creating.value = true
  try {
    const book = await booksApi.create(title)
    createTitle.value = ''
    await loadBooks()
    activePageId.value = null
    applyBook(book)
  } finally {
    creating.value = false
  }
}

async function saveBookTitle() {
  if (!selected.value) return
  savingBook.value = true
  try {
    await booksApi.update(selected.value.id, editorTitle.value.trim())
    selected.value.title = editorTitle.value.trim()
    await loadBooks()
  } finally {
    savingBook.value = false
  }
}

async function deleteBook() {
  if (!selected.value) return
  if (!window.confirm(`确定删除《${selected.value.title}》及其全部页面吗？`)) return
  await booksApi.remove(selected.value.id)
  selected.value = null
  activePageId.value = null
  await loadBooks()
}

function selectPage(id: number) {
  const page = selected.value?.pages.find((item) => item.id === id)
  if (page) applyPage(page)
}

async function savePage() {
  if (!selected.value || !currentPage.value) return
  savingPage.value = true
  try {
    const book = await booksApi.updatePage(selected.value.id, currentPage.value.id, {
      content: pageContent.value,
      image: pageImage.value,
    })
    applyBook(book)
    await loadBooks()
  } finally {
    savingPage.value = false
  }
}

async function insertPageAfter() {
  if (!selected.value || !currentPage.value) return
  const book = await booksApi.addPage(selected.value.id, {
    content: '',
    image: null,
    after_page_id: currentPage.value.id,
  })
  applyBook(book)
  const inserted = book.pages.find((page) => page.position === currentPage.value!.position + 1)
  if (inserted) applyPage(inserted)
  await loadBooks()
}

async function deletePage() {
  if (!selected.value || !currentPage.value || selected.value.pages.length <= 1) return
  if (!window.confirm(`确定删除第 ${currentPage.value.position} 页吗？`)) return
  const book = await booksApi.removePage(selected.value.id, currentPage.value.id)
  applyBook(book)
  await loadBooks()
}

async function uploadImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const result = await booksApi.uploadImage(file)
    pageImage.value = result.path
  } finally {
    uploading.value = false
    input.value = ''
  }
}

onMounted(loadBooks)
</script>

<style scoped>
.book-admin {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.admin-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
}

.hint {
  margin-top: 5px;
  color: var(--muted);
  font-size: 12px;
}

.create-row {
  display: flex;
  gap: 10px;
  min-width: min(440px, 48%);
}

.create-row input,
.title-input,
.field textarea {
  width: 100%;
  border: 1px solid var(--line2);
  border-radius: 6px;
  background: var(--bg2);
  color: var(--text);
  outline: none;
}

.create-row input,
.title-input {
  padding: 9px 12px;
}

.create-row input:focus,
.title-input:focus,
.field textarea:focus {
  border-color: var(--green);
}

.book-layout {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  min-height: 540px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
}

.book-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  border-right: 1px solid var(--line);
  background: var(--panel2);
}

.book-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
  padding: 10px 11px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  text-align: left;
  cursor: pointer;
}

.book-item:hover,
.book-item.active {
  border-color: rgba(var(--green-rgb), 0.32);
  background: rgba(var(--green-rgb), 0.06);
}

.book-title {
  color: var(--text-strong);
  font-size: 13px;
  font-weight: 700;
}

.book-meta {
  color: var(--dim);
  font-family: var(--mono);
  font-size: 10px;
}

.book-editor {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.book-title-row {
  display: flex;
  gap: 10px;
  padding: 14px;
  border-bottom: 1px solid var(--line);
}

.title-input {
  flex: 1;
  font-size: 15px;
  font-weight: 700;
}

.page-layout {
  display: grid;
  flex: 1;
  grid-template-columns: 128px minmax(0, 1fr);
}

.page-list {
  padding: 10px;
  border-right: 1px solid var(--line);
  background: var(--panel-soft);
}

.page-item {
  width: 100%;
  padding: 8px 10px;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 11px;
  text-align: left;
  cursor: pointer;
}

.page-item:hover,
.page-item.active {
  background: rgba(var(--green-rgb), 0.08);
  color: var(--green);
}

.page-editor {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 11px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--muted);
  font-size: 12px;
}

.field textarea {
  padding: 12px;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.7;
  resize: vertical;
}

.image-row,
.page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.upload-btn {
  padding: 8px 13px;
  border: 1px solid var(--line2);
  border-radius: 6px;
  background: var(--panel);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
}

.upload-btn input {
  display: none;
}

.image-preview {
  max-width: 400px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 6px;
}

.image-preview img {
  display: block;
  width: 100%;
  max-height: 260px;
  object-fit: contain;
  background: var(--bg2);
}

.page-actions {
  margin-top: auto;
  padding-top: 4px;
}

.btn.danger {
  border-color: rgba(var(--red-rgb), 0.45);
  color: var(--red);
}

.btn:disabled {
  opacity: 0.45;
  cursor: default;
}

.book-empty,
.empty {
  display: grid;
  place-items: center;
  min-height: 120px;
  color: var(--dim);
  font-size: 12px;
}

.book-empty {
  min-height: 540px;
}

@media (max-width: 980px) {
  .admin-head {
    align-items: stretch;
    flex-direction: column;
  }

  .create-row {
    min-width: 0;
  }

  .book-layout {
    grid-template-columns: 190px minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .book-layout {
    grid-template-columns: 1fr;
  }

  .book-list {
    max-height: 180px;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .page-layout {
    grid-template-columns: 1fr;
  }

  .page-list {
    display: flex;
    overflow-x: auto;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .page-item {
    width: auto;
    white-space: nowrap;
  }
}
</style>
