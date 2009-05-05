// WinViewTestView.cpp : implementation of the CWinViewTestView class
//

#include "stdafx.h"
#include "WinViewTest.h"

#include "WinViewTestDoc.h"
#include "WinViewTestView.h"

#include "ViewStateMachine.h"
#include "ViewEventHandler.h"
#include "swl/winview/GdiContext.h"
#include "swl/winview/GdiBitmapBufferedContext.h"
#include "swl/winview/GdiplusContext.h"
#include "swl/winview/GdiplusBitmapBufferedContext.h"
#include "swl/view/MouseEvent.h"
#include "swl/view/KeyEvent.h"
#include "swl/view/ViewCamera2.h"
#include "swl/winutil/WinTimer.h"
#include <gdiplus.h>
#include <cmath>

#ifdef _DEBUG
#define new DEBUG_NEW
#endif


// CWinViewTestView

IMPLEMENT_DYNCREATE(CWinViewTestView, CView)

BEGIN_MESSAGE_MAP(CWinViewTestView, CView)
	// Standard printing commands
	ON_COMMAND(ID_FILE_PRINT, &CView::OnFilePrint)
	ON_COMMAND(ID_FILE_PRINT_DIRECT, &CView::OnFilePrint)
	ON_COMMAND(ID_FILE_PRINT_PREVIEW, &CView::OnFilePrintPreview)
	ON_WM_TIMER()
	ON_WM_SIZE()
	ON_WM_PAINT()
	ON_WM_LBUTTONDOWN()
	ON_WM_LBUTTONUP()
	ON_WM_LBUTTONDBLCLK()
	ON_WM_MBUTTONDOWN()
	ON_WM_MBUTTONUP()
	ON_WM_MBUTTONDBLCLK()
	ON_WM_RBUTTONDOWN()
	ON_WM_RBUTTONUP()
	ON_WM_RBUTTONDBLCLK()
	ON_WM_MOUSEMOVE()
	ON_WM_MOUSEWHEEL()
	ON_WM_KEYDOWN()
	ON_WM_KEYUP()
	ON_WM_CHAR()
	ON_COMMAND(ID_VIEWSTATE_PAN, &CWinViewTestView::OnViewstatePan)
	ON_COMMAND(ID_VIEWSTATE_ROTATE, &CWinViewTestView::OnViewstateRotate)
	ON_COMMAND(ID_VIEWSTATE_ZOOMREGION, &CWinViewTestView::OnViewstateZoomregion)
	ON_COMMAND(ID_VIEWSTATE_ZOOMALL, &CWinViewTestView::OnViewstateZoomall)
	ON_COMMAND(ID_VIEWSTATE_ZOOMIN, &CWinViewTestView::OnViewstateZoomin)
	ON_COMMAND(ID_VIEWSTATE_ZOOMOUT, &CWinViewTestView::OnViewstateZoomout)
	ON_UPDATE_COMMAND_UI(ID_VIEWSTATE_PAN, &CWinViewTestView::OnUpdateViewstatePan)
	ON_UPDATE_COMMAND_UI(ID_VIEWSTATE_ROTATE, &CWinViewTestView::OnUpdateViewstateRotate)
	ON_UPDATE_COMMAND_UI(ID_VIEWSTATE_ZOOMREGION, &CWinViewTestView::OnUpdateViewstateZoomregion)
	ON_UPDATE_COMMAND_UI(ID_VIEWSTATE_ZOOMALL, &CWinViewTestView::OnUpdateViewstateZoomall)
	ON_UPDATE_COMMAND_UI(ID_VIEWSTATE_ZOOMIN, &CWinViewTestView::OnUpdateViewstateZoomin)
	ON_UPDATE_COMMAND_UI(ID_VIEWSTATE_ZOOMOUT, &CWinViewTestView::OnUpdateViewstateZoomout)
END_MESSAGE_MAP()

// CWinViewTestView construction/destruction

CWinViewTestView::CWinViewTestView()
: viewContext_(), viewCamera_(), viewStateFsm_()
{
}

CWinViewTestView::~CWinViewTestView()
{
}

BOOL CWinViewTestView::PreCreateWindow(CREATESTRUCT& cs)
{
	// TODO: Modify the Window class or styles here by modifying
	//  the CREATESTRUCT cs

	return CView::PreCreateWindow(cs);
}

// CWinViewTestView drawing

void CWinViewTestView::OnDraw(CDC* pDC)
{
	CWinViewTestDoc* pDoc = GetDocument();
	ASSERT_VALID(pDoc);
	if (!pDoc)
		return;

	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: basic routine

	if (pDC && pDC->IsPrinting())
	{
		// FIXME [add] >>
	}
	else
	{
		switch (drawMode_)
		{
		case 1:
			test1();
			break;
		case 2:
			test2();
			break;
		case 3:
			test3();
			break;
		case 4:
			test4();
			break;
		case 5:
			test5();
			break;
		}
	}
}


// CWinViewTestView printing

BOOL CWinViewTestView::OnPreparePrinting(CPrintInfo* pInfo)
{
	// default preparation
	return DoPreparePrinting(pInfo);
}

void CWinViewTestView::OnBeginPrinting(CDC* /*pDC*/, CPrintInfo* /*pInfo*/)
{
	// TODO: add extra initialization before printing
}

void CWinViewTestView::OnEndPrinting(CDC* /*pDC*/, CPrintInfo* /*pInfo*/)
{
	// TODO: add cleanup after printing
}


// CWinViewTestView diagnostics

#ifdef _DEBUG
void CWinViewTestView::AssertValid() const
{
	CView::AssertValid();
}

void CWinViewTestView::Dump(CDumpContext& dc) const
{
	CView::Dump(dc);
}

CWinViewTestDoc* CWinViewTestView::GetDocument() const // non-debug version is inline
{
	ASSERT(m_pDocument->IsKindOf(RUNTIME_CLASS(CWinViewTestDoc)));
	return (CWinViewTestDoc*)m_pDocument;
}
#endif //_DEBUG


// CWinViewTestView message handlers

void CWinViewTestView::OnInitialUpdate()
{
	CView::OnInitialUpdate();

	//
	drawMode_ = 5;  // [1, 5]

	idx_ = 0;
	timeInterval_ = 50;
	//SetTimer(1, timeInterval_, NULL);

	for (int i = 0; i < 5000; ++i)
	{
		const double x = (double)i * timeInterval_ / 1000.0;
		const double y = std::sin(x) * 100.0 + 100.0;
		data1_.push_back(std::make_pair(i, (int)std::floor(y + 0.5)));
	}

	CRect rect;
	GetClientRect(&rect);

	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling

	viewController_.addMousePressHandler(swl::MousePressHandler());
	viewController_.addMouseReleaseHandler(swl::MouseReleaseHandler());
	viewController_.addMouseMoveHandler(swl::MouseMoveHandler());
	viewController_.addMouseWheelHandler(swl::MouseWheelHandler());
	viewController_.addMouseClickHandler(swl::MouseClickHandler());
	viewController_.addMouseDoubleClickHandler(swl::MouseDoubleClickHandler());
	viewController_.addKeyPressHandler(swl::KeyPressHandler());
	viewController_.addKeyReleaseHandler(swl::KeyReleaseHandler());
	viewController_.addKeyHitHandler(swl::KeyHitHandler());

	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: basic routine

	// create a context
	if (5 == drawMode_ && NULL == viewContext_.get())
	{
		viewContext_.reset(new swl::GdiplusBitmapBufferedContext(GetSafeHwnd(), rect, false));
	}

	// create a camera
	if (NULL == viewCamera_.get())
		viewCamera_.reset(new swl::ViewCamera2());

	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state

	if (NULL == viewStateFsm_.get() && NULL != viewContext_.get() && NULL != viewCamera_.get())
	{
		viewStateFsm_.reset(new swl::ViewStateMachine(*this, *viewContext_, *viewCamera_));
		if (viewStateFsm_.get()) viewStateFsm_->initiate();
	}

	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: basic routine

	// initialize a view
	if (viewContext_.get())
	{
		// activate the context
		viewContext_->activate();

		// set the view
		initializeView();

		// set the camera
		if (viewCamera_.get())
		{
			// TODO [check] >>
			viewCamera_->setViewBound(0, 0, rect.Width(), rect.Height());
			viewCamera_->setViewport(0, 0, rect.Width(), rect.Height());
		}

		raiseDrawEvent(false);

		// de-activate the context
		viewContext_->deactivate();
	}
}

void CWinViewTestView::OnPaint()
{
	CPaintDC dc(this); // device context for painting

	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: basic routine

	if (1 <= drawMode_ && drawMode_ <= 4)
	{
		raiseDrawEvent(true);
	}
	else if (5 == drawMode_)
	{
		if (viewContext_.get())
		{
			if (viewContext_->isOffScreenUsed())
			{
				//viewContext_->activate();
				viewContext_->swapBuffer();
				//viewContext_->deactivate();
			}
			else raiseDrawEvent(true);
		}
	}

	// Do not call CView::OnPaint() for painting messages
}

void CWinViewTestView::OnTimer(UINT_PTR nIDEvent)
{
	// TODO: Add your message handler code here and/or call default
	const double x = (double)idx_ * timeInterval_ / 1000.0;
	const double y = std::cos(x) * 100.0 + 100.0;
	data2_.push_back(std::make_pair(idx_, (int)std::floor(y + 0.5)));

	++idx_;

	if (1 <= drawMode_ && drawMode_ <= 4)
	{
		OnDraw(0L);
	}
	else if (5 == drawMode_)
	{
		raiseDrawEvent(true);
	}

	CView::OnTimer(nIDEvent);
}

void CWinViewTestView::OnSize(UINT nType, int cx, int cy)
{
	CView::OnSize(nType, cx, cy);

	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: basic routine

	if (cx <= 0 || cy <= 0) return;

	if (1 <= drawMode_ && drawMode_ <= 4)
	{
		// do nothing
	}
	else if (5 == drawMode_)
	{
		resizeView(0, 0, cx, cy);
	}
}

//-------------------------------------------------------------------------
// This code is required for SWL.WinView: basic routine

bool CWinViewTestView::raiseDrawEvent(const bool isContextActivated)
{
	if (NULL == viewContext_.get() || viewContext_->isDrawing())
		return false;

	if (isContextActivated)
	{
		viewContext_->activate();
		OnDraw(0L);
		viewContext_->deactivate();
	}
	else OnDraw(0L);

	return true;
}

//-------------------------------------------------------------------------
// This code is required for SWL.WinView: basic routine

bool CWinViewTestView::initializeView()
{
	return true;
}

//-------------------------------------------------------------------------
// This code is required for SWL.WinView: basic routine

bool CWinViewTestView::resizeView(const int x1, const int y1, const int x2, const int y2)
{
	if (viewContext_.get() && viewContext_->resize(x1, y1, x2, y2))
	{
		viewContext_->activate();
		initializeView();
		if (viewCamera_.get()) viewCamera_->setViewport(x1, y1, x2, y2);	
		raiseDrawEvent(false);
		viewContext_->deactivate();

		return true;
	}
	else return false;
}

// use single-buffered GDI context
void CWinViewTestView::test1()
{
	// create a context
	swl::GdiContext ctx(GetSafeHwnd());
	HDC *dc = static_cast<HDC *>(ctx.getNativeContext());

	if (dc)
	{
		CDC *pDC = CDC::FromHandle(*dc);

		// clear the background
		//pDC->SetBkColor(RGB(192, 192, 0));  // not working ???
		//pDC->FillRect(rect, &CBrush(RGB(192, 192, 0)));

		// draw contents
		{
			CPen pen(PS_SOLID, 2, RGB(255, 0, 0));
			pDC->SelectObject(&pen);
			pDC->MoveTo(100, 100);
			pDC->LineTo(300, 300);
		}

		if (data1_.size() > 1)
		{
			CPen pen(PS_SOLID, 3, RGB(0, 255, 0));
			pDC->SelectObject(&pen);
			data_type::iterator it = data1_.begin();
			pDC->MoveTo(it->first, it->second);
			for (++it; it != data1_.end(); ++it)
				pDC->LineTo(it->first, it->second);
		}

		if (data2_.size() > 1)
		{
			CPen pen(PS_SOLID, 3, RGB(0, 0, 255));
			pDC->SelectObject(&pen);
			data_type::iterator it = data2_.begin();
			pDC->MoveTo(it->first, it->second);
			for (++it; it != data2_.end(); ++it)
				pDC->LineTo(it->first, it->second);
		}
	}

	// swap buffers
	ctx.swapBuffer();
}

// use double(bitmap)-buffered GDI context
void CWinViewTestView::test2()
{
	CRect rect;
	GetClientRect(&rect);

	// create a context
	swl::GdiBitmapBufferedContext ctx(GetSafeHwnd(), rect);
	HDC *dc = static_cast<HDC *>(ctx.getNativeContext());

	if (dc)
	{
		CDC *pDC = CDC::FromHandle(*dc);

		// clear the background
		//pDC->SetBkColor(RGB(255, 255, 255));  // not working ???
		pDC->FillRect(rect, &CBrush(RGB(255, 255, 255)));
		//pDC->FillRect(rect, &CBrush(GetSysColor(COLOR_WINDOW)));

		// draw contents
		{
			CPen pen(PS_SOLID, 3, RGB(255, 0, 0));
			pDC->SelectObject(&pen);
			pDC->MoveTo(100, 150);
			pDC->LineTo(300, 350);
		}

		if (data1_.size() > 1)
		{
			CPen pen(PS_SOLID, 3, RGB(0, 255, 0));
			pDC->SelectObject(&pen);
			data_type::iterator it = data1_.begin();
			pDC->MoveTo(it->first, it->second);
			for (++it; it != data1_.end(); ++it)
				pDC->LineTo(it->first, it->second);
		}

		if (data2_.size() > 1)
		{
			CPen pen(PS_SOLID, 3, RGB(0, 0, 255));
			pDC->SelectObject(&pen);
			data_type::iterator it = data2_.begin();
			pDC->MoveTo(it->first, it->second);
			for (++it; it != data2_.end(); ++it)
				pDC->LineTo(it->first, it->second);
		}
	}

	// swap buffers
	ctx.swapBuffer();
}

// use single-buffered GDI+ context
void CWinViewTestView::test3()
{
	// create a context
	swl::GdiplusContext ctx(GetSafeHwnd());
	Gdiplus::Graphics *graphics = static_cast<Gdiplus::Graphics *>(ctx.getNativeContext());

	if (graphics)
	{
		// clear the background
		//graphics->Clear(Gdiplus::Color(255, 192, 0, 192));

		// draw contents
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 255, 0, 0), 4.0f);
			graphics->DrawLine(&pen, 100, 200, 300, 400);
		}

		if (data1_.size() > 1)
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 0, 255, 0), 4.0f);
			data_type::iterator prevIt = data1_.begin();
			data_type::iterator it = data1_.begin();
			for (++it; it != data1_.end(); ++prevIt, ++it)
				graphics->DrawLine(&pen, (Gdiplus::REAL)prevIt->first, (Gdiplus::REAL)prevIt->second, (Gdiplus::REAL)it->first, (Gdiplus::REAL)it->second);
		}

		if (data2_.size() > 1)
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 0, 0, 255), 4.0f);
			data_type::iterator prevIt = data2_.begin();
			data_type::iterator it = data2_.begin();
			for (++it; it != data2_.end(); ++prevIt, ++it)
				graphics->DrawLine(&pen, (Gdiplus::REAL)prevIt->first, (Gdiplus::REAL)prevIt->second, (Gdiplus::REAL)it->first, (Gdiplus::REAL)it->second);
		}
	}

	// swap buffers
	ctx.swapBuffer();
}

// use double(bitmap)-buffered GDI+ context
void CWinViewTestView::test4()
{
	CRect rect;
	GetClientRect(&rect);

	// create a context
	swl::GdiplusBitmapBufferedContext ctx(GetSafeHwnd(), rect);
	Gdiplus::Graphics *graphics = static_cast<Gdiplus::Graphics *>(ctx.getNativeContext());

	if (graphics)
	{
		// clear the background
		//graphics->Clear(Gdiplus::Color(255, 0, 192, 192));

		// draw contents
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 255, 0, 0), 5.0f);
			graphics->DrawLine(&pen, 100, 250, 300, 450);
		}

		if (data1_.size() > 1)
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 0, 255, 0), 5.0f);
			data_type::iterator prevIt = data1_.begin();
			data_type::iterator it = data1_.begin();
			for (++it; it != data1_.end(); ++prevIt, ++it)
				graphics->DrawLine(&pen, (Gdiplus::REAL)prevIt->first, (Gdiplus::REAL)prevIt->second, (Gdiplus::REAL)it->first, (Gdiplus::REAL)it->second);
		}

		if (data2_.size() > 1)
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 0, 0, 255), 5.0f);
			data_type::iterator prevIt = data2_.begin();
			data_type::iterator it = data2_.begin();
			for (++it; it != data2_.end(); ++prevIt, ++it)
				graphics->DrawLine(&pen, (Gdiplus::REAL)prevIt->first, (Gdiplus::REAL)prevIt->second, (Gdiplus::REAL)it->first, (Gdiplus::REAL)it->second);
		}
	}

	// swap buffers
	ctx.swapBuffer();
}

// use double(bitmap)-buffered GDI+ context
void CWinViewTestView::test5()
{
	CRect rect;
	GetClientRect(&rect);

	// activate a context
	viewContext_->activate();

	Gdiplus::Graphics *graphics = static_cast<Gdiplus::Graphics *>(viewContext_->getNativeContext());

	if (graphics)
	{
		// clear the background
		//graphics->Clear(Gdiplus::Color(255, 0, 192, 192));

		// draw contents
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 255, 0, 0), 6.0f);
			graphics->DrawLine(&pen, 100, 300, 300, 500);
		}

		if (data1_.size() > 1)
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 0, 255, 0), 6.0f);
			data_type::iterator prevIt = data1_.begin();
			data_type::iterator it = data1_.begin();
			for (++it; it != data1_.end(); ++prevIt, ++it)
				graphics->DrawLine(&pen, (Gdiplus::REAL)prevIt->first, (Gdiplus::REAL)prevIt->second, (Gdiplus::REAL)it->first, (Gdiplus::REAL)it->second);
		}

		if (data2_.size() > 1)
		{
			Gdiplus::Pen pen(Gdiplus::Color(255, 0, 0, 255), 6.0f);
			data_type::iterator prevIt = data2_.begin();
			data_type::iterator it = data2_.begin();
			for (++it; it != data2_.end(); ++prevIt, ++it)
				graphics->DrawLine(&pen, (Gdiplus::REAL)prevIt->first, (Gdiplus::REAL)prevIt->second, (Gdiplus::REAL)it->first, (Gdiplus::REAL)it->second);
		}
	}

	// swap buffers
	viewContext_->swapBuffer();

	// de-activate the context
	viewContext_->deactivate();
}

void CWinViewTestView::OnLButtonDown(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	SetCapture();

	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.pressMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_LEFT, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->pressMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_LEFT, ckey));

	CView::OnLButtonDown(nFlags, point);
}

void CWinViewTestView::OnLButtonUp(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	ReleaseCapture();

	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.releaseMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_LEFT, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->releaseMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_LEFT, ckey));

	CView::OnLButtonUp(nFlags, point);
}

void CWinViewTestView::OnLButtonDblClk(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.doubleClickMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_LEFT, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->doubleClickMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_LEFT, ckey));

	CView::OnLButtonDblClk(nFlags, point);
}

void CWinViewTestView::OnMButtonDown(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	SetCapture();

	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.pressMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_MIDDLE, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->pressMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_MIDDLE, ckey));

	CView::OnMButtonDown(nFlags, point);
}

void CWinViewTestView::OnMButtonUp(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	ReleaseCapture();

	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.releaseMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_MIDDLE, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->releaseMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_MIDDLE, ckey));

	CView::OnMButtonUp(nFlags, point);
}

void CWinViewTestView::OnMButtonDblClk(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.doubleClickMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_MIDDLE, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->doubleClickMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_MIDDLE, ckey));

	CView::OnMButtonDblClk(nFlags, point);
}

void CWinViewTestView::OnRButtonDown(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	SetCapture();

	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.pressMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->pressMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey));

	CView::OnRButtonDown(nFlags, point);
}

void CWinViewTestView::OnRButtonUp(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	ReleaseCapture();

	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.releaseMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->releaseMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey));

	CView::OnRButtonUp(nFlags, point);
}

void CWinViewTestView::OnRButtonDblClk(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.doubleClickMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->doubleClickMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey));

	CView::OnRButtonDblClk(nFlags, point);
}

void CWinViewTestView::OnMouseMove(UINT nFlags, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.moveMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->moveMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey));

	CView::OnMouseMove(nFlags, point);
}

BOOL CWinViewTestView::OnMouseWheel(UINT nFlags, short zDelta, CPoint point)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	// TODO [check] >>
	const swl::MouseEvent::EControlKey ckey = (swl::MouseEvent::EControlKey)(
		((nFlags | MK_CONTROL) == MK_CONTROL ? swl::MouseEvent::CK_CTRL : swl::MouseEvent::CK_NONE) |
		((nFlags | MK_SHIFT) == MK_SHIFT ? swl::MouseEvent::CK_SHIFT : swl::MouseEvent::CK_NONE)
	);
	//viewController_.wheelMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey, swl::MouseEvent::SC_HORIZONTAL, zDelta));
	if (viewStateFsm_.get()) viewStateFsm_->wheelMouse(swl::MouseEvent(point.x, point.y, swl::MouseEvent::BT_RIGHT, ckey, swl::MouseEvent::SC_VERTICAL, zDelta));

	return CView::OnMouseWheel(nFlags, zDelta, point);
}

void CWinViewTestView::OnKeyDown(UINT nChar, UINT nRepCnt, UINT nFlags)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	//viewController_.pressKey(swl::KeyEvent(nChar, nRepCnt));
	if (viewStateFsm_.get()) viewStateFsm_->pressKey(swl::KeyEvent(nChar, nRepCnt));

	CView::OnKeyDown(nChar, nRepCnt, nFlags);
}

void CWinViewTestView::OnKeyUp(UINT nChar, UINT nRepCnt, UINT nFlags)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	//viewController_.releaseKey(swl::KeyEvent(nChar, nRepCnt));
	if (viewStateFsm_.get()) viewStateFsm_->releaseKey(swl::KeyEvent(nChar, nRepCnt));

	CView::OnKeyUp(nChar, nRepCnt, nFlags);
}

void CWinViewTestView::OnChar(UINT nChar, UINT nRepCnt, UINT nFlags)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: event handling
	// TODO [check] >>
	const swl::KeyEvent::EControlKey ckey = ((nFlags >> 28) & 0x01) == 0x01 ? swl::KeyEvent::CK_ALT : swl::KeyEvent::CK_NONE;
	//viewController_.releaseKey(swl::KeyEvent(nChar, nRepCnt, ckey));
	if (viewStateFsm_.get()) viewStateFsm_->releaseKey(swl::KeyEvent(nChar, nRepCnt, ckey));

	CView::OnChar(nChar, nRepCnt, nFlags);
}

void CWinViewTestView::OnViewstatePan()
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get()) viewStateFsm_->process_event(swl::EvtPan());
}

void CWinViewTestView::OnViewstateRotate()
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get()) viewStateFsm_->process_event(swl::EvtRotate());
}

void CWinViewTestView::OnViewstateZoomregion()
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get()) viewStateFsm_->process_event(swl::EvtZoomRegion());
}

void CWinViewTestView::OnViewstateZoomall()
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get()) viewStateFsm_->process_event(swl::EvtZoomAll());
}

void CWinViewTestView::OnViewstateZoomin()
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get()) viewStateFsm_->process_event(swl::EvtZoomIn());
}

void CWinViewTestView::OnViewstateZoomout()
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get()) viewStateFsm_->process_event(swl::EvtZoomOut());
}

void CWinViewTestView::OnUpdateViewstatePan(CCmdUI *pCmdUI)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get())
	{
		const swl::PanState *active = viewStateFsm_->state_cast<const swl::PanState *>();
		pCmdUI->SetCheck(active ? 1 : 0);
	}
	else pCmdUI->SetCheck(0);
}

void CWinViewTestView::OnUpdateViewstateRotate(CCmdUI *pCmdUI)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get())
	{
		const swl::RotateState *active = viewStateFsm_->state_cast<const swl::RotateState *>();
		pCmdUI->SetCheck(active ? 1 : 0);
	}
	else pCmdUI->SetCheck(0);
}

void CWinViewTestView::OnUpdateViewstateZoomregion(CCmdUI *pCmdUI)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get())
	{
		const swl::ZoomRegionState *active = viewStateFsm_->state_cast<const swl::ZoomRegionState *>();
		pCmdUI->SetCheck(active ? 1 : 0);
	}
	else pCmdUI->SetCheck(0);
}

void CWinViewTestView::OnUpdateViewstateZoomall(CCmdUI *pCmdUI)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get())
	{
		const swl::ZoomAllState *active = viewStateFsm_->state_cast<const swl::ZoomAllState *>();
		pCmdUI->SetCheck(active ? 1 : 0);
	}
	else pCmdUI->SetCheck(0);
}

void CWinViewTestView::OnUpdateViewstateZoomin(CCmdUI *pCmdUI)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get())
	{
		const swl::ZoomInState *active = viewStateFsm_->state_cast<const swl::ZoomInState *>();
		pCmdUI->SetCheck(active ? 1 : 0);
	}
	else pCmdUI->SetCheck(0);
}

void CWinViewTestView::OnUpdateViewstateZoomout(CCmdUI *pCmdUI)
{
	//-------------------------------------------------------------------------
	// This code is required for SWL.WinView: view state
	if (viewStateFsm_.get())
	{
		const swl::ZoomOutState *active = viewStateFsm_->state_cast<const swl::ZoomOutState *>();
		pCmdUI->SetCheck(active ? 1 : 0);
	}
	else pCmdUI->SetCheck(0);
}
