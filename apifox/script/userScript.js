// ==UserScript==
// @name         Convert title to kebab-case
// @namespace    https://github.com/gildas-lormeau/SingleFile
// @version      1.0
// @description  [SingleFile] Convert title to kebab-case
// @author       Gildas Lormeau
// @match        *://*/*
// @noframes
// @grant        none
// ==/UserScript==



(() => {
  dispatchEvent(new CustomEvent("single-file-user-script-init"));

  // 函数：处理具有 rotate(270deg) 的 <svg> 元素
  function handleRotatedSVGs() {
    // 获取所有的 <svg> 元素
    const svgs = document.querySelectorAll('svg');

    // 遍历每个 <svg> 元素，找到具有 transform: rotate(270deg) 的元素
    const rotatedSvgs = Array.from(svgs).filter(svg => {
      const transform = svg.style.transform; // 获取 style 中的 transform 属性
      return transform.includes('rotate(270deg)'); // 检查是否包含 rotate(270deg)
    });

    // 触发符合条件的 <svg> 的点击事件
    rotatedSvgs.forEach(svg => {
      const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window
      });
      svg.dispatchEvent(clickEvent); // 通过 dispatchEvent 触发点击事件
    });
  }


  // 函数：处理主题切换按钮
  function handleThemeToggle() {
    // 找到 title="Toggle theme" 的按钮元素
    const toggleThemeButton = document.querySelector('button[title="Toggle theme"]');

    // 判断按钮的 class 列表中是否包含 "theme-toggle--toggled"
    if (toggleThemeButton && toggleThemeButton.classList.contains('theme-toggle--toggled')) {
      // 如果包含，则触发按钮的点击事件
      toggleThemeButton.click();
    }
  }

  // 删除多余的svg
  function removeSVGsFromBody() {
    const body = document.body;

    // 找到 <body> 直接子元素中的所有 SVG 元素
    const svgs = Array.from(body.children).filter(child => child.tagName.toLowerCase() === 'svg');

    // 删除 SVG 元素
    svgs.forEach(svg => {
      body.removeChild(svg);
    });
  }

  // 
  function removeDivByClass(className) {
    // 找到所有具有指定 class 的 div 元素
    const divs = document.querySelectorAll(`div.${className}`);

    // 删除这些 div 元素
    divs.forEach(div => {
        div.parentNode.removeChild(div);
    });
  }

  // 函数：向 document 增加 scrollToExactActiveLink 脚本
  function injectScrollScript() {
    const script = document.createElement('script');
    script.textContent = `
      function scrollToExactActiveLink() {
        const links = document.querySelectorAll('a.menu__link.menu__link--active');
        const exactActiveLink = Array.from(links).find(link => link.classList.length === 2);
        if (exactActiveLink) {
          exactActiveLink.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        } else {
          console.log('未找到仅包含 class="menu__link menu__link--active" 的 <a> 元素');
        }
      }
      window.onload = scrollToExactActiveLink;
    `;
    document.head.appendChild(script);
  }

  // 函数：初始化 MutationObserver 以监控 DOM 变化
  function observeDOMChanges() {
    const observer = new MutationObserver((mutationsList) => {
      for (const mutation of mutationsList) {
        if (mutation.type === 'childList' || mutation.type === 'attributes') {
          // 每次有新的子节点被插入，或者属性变化时，重新处理 SVG 元素
          handleRotatedSVGs();
        }
      }
    });

    // 开始观察整个文档中的子节点变化和属性变化
    observer.observe(document.body, { 
      childList: true, // 观察子节点变化
      attributes: true, // 观察属性变化
      subtree: true // 观察整个 DOM 树
    });
  }

  addEventListener("single-file-on-before-capture-request", () => {
    observeDOMChanges();  // 启动对 DOM 变化的监控，便于递归调用handleRotatedSVGs
    handleRotatedSVGs();  // 处理旋转的 SVG 元素
    handleThemeToggle();  // 处理主题切换
    removeSVGsFromBody(); // 删除 SVG 元素
    removeDivByClass('pui-pages-shared-doc-sider-index-search-select'); // 删除搜索框
  });

  addEventListener("single-file-on-after-capture-request", () => {
  });

})();


function scrollToExactActiveLink() {
  const sidebar = document.querySelector('.pui-pages-main-tree-list-index-content__tree.overflow-y-scroll.h-full');
  console.log(sidebar);

  // 获取所有 class 包含 "menu__link" 和 "menu__link--active" 的 <a> 元素
  const links = document.querySelectorAll('a.menu__link.menu__link--active');

  // 找到 class 只有 "menu__link" 和 "menu__link--active" 的 <a> 元素
  const exactActiveLink = Array.from(links).find(link => {
      // 检查该 <a> 的 classList 是否正好包含 2 个类
      return link.classList.length === 2;
  });

  if (exactActiveLink) {
      console.log('找到仅包含 class="menu__link menu__link--active" 的 <a> 元素', exactActiveLink);
      // 计算 <a> 在 sidebar 中的相对位置
      const linkRect = exactActiveLink.getBoundingClientRect();
      const sidebarRect = sidebar.getBoundingClientRect();
      
      // 计算目标位置
      const targetScrollTop = linkRect.top - sidebarRect.top + sidebar.scrollTop - 39;
      console.log(targetScrollTop);
      
      // 滚动 sidebar 到目标位置
      sidebar.scrollTo({
          top: targetScrollTop,
          behavior: 'smooth'  // 平滑滚动
      });
  } else {
      console.log('未找到仅包含 class="menu__link menu__link--active" 的 <a> 元素');
  }
}